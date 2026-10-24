import json, datetime, sys, time
from pathlib import Path
import gmpy2

CHUNK = 100_000
DATA_DIR = Path("pi_data")
INDEX_FILE = DATA_DIR / "index.json"
PROGRESS_FILE = DATA_DIR / "progress.json"

def cli_log(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

def update_progress_cli(**kw):
    DATA_DIR.mkdir(exist_ok=True)
    data = json.loads(PROGRESS_FILE.read_text()) if PROGRESS_FILE.exists() else {}
    data.update(kw)
    data["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    PROGRESS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    # コマンドラインに進捗を出す
    total = data.get("total_digits", 0)
    status = data.get("status", "?")
    print(f"\r[CLI PROGRESS] {status} | total={total:,} digits | {kw}", end="", flush=True)
    if kw.get("status") in ["computed", "waiting_next"]:
        print() # 改行

def compute_pi_digits(n):
    cli_log(f"Start Chudnovsky computation for {n:,} digits")
    gmpy2.get_context().precision = int(n * 3.5 + 100)
    
    C = 426880 * gmpy2.sqrt(gmpy2.mpz(10005))
    M = gmpy2.mpz(1)
    L = gmpy2.mpz(13591409)
    X = gmpy2.mpz(1)
    K = gmpy2.mpz(6)
    S = L
    
    target_iter = n // 14 + 10
    start_time = time.time()
    
    for i in range(1, target_iter):
        # 100回ごとにCLI表示
        if i % 100 == 0 or i == 1:
            elapsed = time.time() - start_time
            percent = i / target_iter * 100
            # \r で同じ行を上書き
            sys.stdout.write(f"\r[COMPUTING] {i}/{target_iter} ({percent:.1f}%) elapsed={elapsed:.1f}s ")
            sys.stdout.flush()
            if i % 500 == 0:
                update_progress_cli(status="computing", iter=f"{i}/{target_iter}", percent=f"{percent:.1f}%")

        M = (K**3 - 16*K) * M // (i**3)
        L += 545140134
        X *= -262537412640768000
        S += M * L / X
        K += 12

    sys.stdout.write("\n")
    cli_log("Final division...")
    pi = C / S
    frac = (str(pi).split('.')[1] + '0'*n)[:n]
    cli_log(f"Computation done: {len(frac):,} digits")
    return frac

def main():
    DATA_DIR.mkdir(exist_ok=True)
    total = json.loads(INDEX_FILE.read_text()).get("total_digits", 0) if INDEX_FILE.exists() else 0
    
    cli_log(f"=== Pi Calculator ===")
    cli_log(f"Current total: {total:,} digits")
    cli_log(f"Next range: {total+1:,} - {total+CHUNK:,}")

    update_progress_cli(
        total_digits=total,
        status="start_computing",
        next_range=f"{total+1}-{total+CHUNK}",
        total_files=len(list(DATA_DIR.glob("pi_*.txt")))
    )

    full_frac = compute_pi_digits(total + CHUNK)
    new_chunk = full_frac[total:total+CHUNK]

    out_file = DATA_DIR / f"pi_{total+1:08d}-{total+CHUNK:08d}.txt"
    out_file.write_text(new_chunk)
    
    INDEX_FILE.write_text(json.dumps({"total_digits": total+CHUNK}, indent=2))
    
    # プロセス終了前に必ず最終更新
    update_progress_cli(
        total_digits=total+CHUNK,
        status="computed",
        last_file=str(out_file.name),
        total_files=len(list(DATA_DIR.glob("pi_*.txt")))
    )
    cli_log(f"Saved: {out_file.name} ({len(new_chunk):,} digits)")
    cli_log(f"New total: {total+CHUNK:,} digits")

if __name__ == "__main__":
    main()
