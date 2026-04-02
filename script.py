import requests
import itertools
import os
import random
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

os.chdir(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = "username.txt"
WORKERS = 10          # SAFE FOR RAILWAY
BATCH_SIZE = 50       # SAFE FOR RAILWAY

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
PINK = "\033[95m"

TAKEN_MESSAGES = [f"{RED}{BOLD}TAKEN{RESET}"]
AVAILABLE_MESSAGES = [f"{GREEN}{BOLD}AVAILABLE{RESET}"]

# ================= DISCORD WEBHOOK =================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1482907849456615566/vSCEElTR1PAkNFoAFFKJdhPYYppOBdXDFUa63DuumnUeG_aq4WgsB8VHqEPwnr_PqIs6"

def send_webhook(name):
    if not DISCORD_WEBHOOK:
        return
    try:
        data = {
            "content": "@everyone",
            "allowed_mentions": {"parse": ["everyone"]},
            "embeds": [{
                "title": "Username Available 🚀",
                "description": f"**@{name}** is AVAILABLE",
                "color": 5763719,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }]
        }
        requests.post(DISCORD_WEBHOOK, json=data, timeout=5)
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")

# ================= VARIANTS =================
def cap_variants(name: str):
    seen = {name}
    yield name

    for v in {name.lower(), name.upper(), name.capitalize()}:
        if v not in seen:
            seen.add(v)
            yield v

    if len(name) <= 6:
        for bits in itertools.product([0, 1], repeat=len(name)):
            v = "".join(
                name[i].upper() if bits[i] else name[i].lower()
                for i in range(len(name))
            )
            if v not in seen:
                seen.add(v)
                yield v

# ================= CHECK LOGIC =================
def single_check(session, variant):
    try:
        r = session.get(
            f"https://horizon.meta.com/profile/{variant}/",
            allow_redirects=False,
            timeout=5
        )
        if r.status_code == 200:
            return "TAKEN"

        if r.status_code in (301, 302):
            return "AVAILABLE" if r.headers.get("Location", "") == "https://horizon.meta.com/" else "TAKEN"

    except:
        pass

    return None

def check_username(idx, name, total):
    name = name.strip().lstrip("@")
    if not name:
        return idx, name, "SKIP"

    session = requests.Session()

    if single_check(session, name) == "TAKEN":
        return idx, name, "TAKEN"

    if single_check(session, name) == "AVAILABLE":
        for v in cap_variants(name):
            if v != name and single_check(session, v) == "TAKEN":
                return idx, name, "TAKEN"
        return idx, name, "AVAILABLE"

    for v in cap_variants(name):
        if v != name and single_check(session, v) == "TAKEN":
            return idx, name, "TAKEN"

    return idx, name, "AVAILABLE"

# ================= MAIN =================
def run_checker():
    print(f"\n{CYAN}{BOLD}{'='*70}{RESET}")
    print(f"{PINK}{BOLD} META USERNAME CHECKER (FAST MODE){RESET}")
    print(f"{CYAN}{BOLD}{'='*70}{RESET}\n")

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            usernames = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{RED}username.txt not found!{RESET}")
        return

    total = len(usernames)
    results = {}
    seen = set()

    batches = [usernames[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]

    for bnum, batch in enumerate(batches, 1):
        print(f"{CYAN}── Batch {bnum}/{len(batches)} ──{RESET}")

        offset = (bnum - 1) * BATCH_SIZE

        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {
                ex.submit(check_username, offset + i, name, total): name
                for i, name in enumerate(batch)
                if name.lower() not in seen and not seen.add(name.lower())
            }

            for fut in as_completed(futures):
                idx, name, status = fut.result()
                results[idx] = (name, status)

                prefix = f"{DIM}[{idx:04}/{total:04}]{RESET} {BOLD}{CYAN}{name:<20}{RESET}"

                if status == "TAKEN":
                    print(f"{prefix} {random.choice(TAKEN_MESSAGES)}", flush=True)
                else:
                    print(f"{prefix} {random.choice(AVAILABLE_MESSAGES)}", flush=True)
                    send_webhook(name)

    taken = [n for n, s in results.values() if s == "TAKEN"]
    available = [n for n, s in results.values() if s == "AVAILABLE"]

    open("available.txt", "w").write("\n".join(available))
    open("taken.txt", "w").write("\n".join(taken))

    print(f"\n{GREEN}AVAILABLE: {len(available)}{RESET}")
    print(f"{RED}TAKEN: {len(taken)}{RESET}")

# ================= 24/7 LOOP =================
def main():
    while True:
        try:
            run_checker()
        except Exception as e:
            print(f"{RED}[CRASH] {e}{RESET}")

        print(f"{DIM}Restarting in 15 seconds...{RESET}")
        time.sleep(15)

if __name__ == "__main__":
    main()
