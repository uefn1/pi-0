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
    print(f"\r[CLI PROGRESS] {kw.get('status')} | total={data.get('total_digits')} | {kw}", end="", flush=True)
    if kw.get("status") in ["computed", "waiting_next"]:
        print()

def compute_pi_digits(n):
    cli_log(f"Start Chudnovsky for {n:,} digits")
    gmpy2.get_context().precision = int(n * 3.5 + 100)
    C = 426880 * gmpy2.sqrt(gmpy2.mpz(10005))
    M, L, X, K, S = gmpy2.mpz(1), gmpy2.mpz(13591409), gmpy2.mpz(1), gmpy2.mpz(6), gmpy2.mpz(13591409)
    target_iter = n // 14 + 10
    start_time = time.time()
    for i in range(1, target_iter):
        if i % 100 == 0 or i == 1:
            elapsed = time.time() - start_time
            percent = i / target_iter * 100
            sys.stdout.write(f"\r[COMPUTING] {i}/{target_iter} ({percent:.1f}%) elapsed={elapsed:.1f}s ")
            sys.stdout.flush()
            if i % 500 == 0:
                update_progress_cli(status="computing", iter=f"{i}/{target_iter}")
        M = (K**3 - 16*K) * M // (i**3)
        L += 545140134
        X *= -262537412640768000
        S += M * L / X
        K += 12
    sys.stdout.write("\n")
    pi = C / S
    s = str(pi)
    # s = "3.14159..."
    return s

def main():
    DATA_DIR.mkdir(exist_ok=True)
    total = json.loads(INDEX_FILE.read_text()).get("total_digits", 0) if INDEX_FILE.exists() else 0
    
    start = total
    end = total + CHUNK - 1
    
    cli_log(f"=== Pi Calculator (with 3.) ===")
    cli_log(f"Current total: {total:,} digits")
    cli_log(f"Next range: {start:,} - {end:,}")

    update_progress_cli(
        total_digits=total,
        status="start_computing",
        next_range=f"{start}-{end}",
        total_files=len(list(DATA_DIR.glob("pi_*.txt")))
    )

    # n = total + CHUNK 桁の小数点以下が必要なので、全体の文字列を取得
    full_pi_str = compute_pi_digits(total + CHUNK) # "3.1415..."
    full_frac = full_pi_str.split('.')[1]
    full_frac = (full_frac + '0'*(total+CHUNK))[:total+CHUNK]
    
    new_chunk_frac = full_frac[start:start+CHUNK]

    # ★ここで 3. を付ける: 最初のファイルだけ
    if start == 0:
        file_content = "3." + new_chunk_frac
        cli_log(f"First file includes integer part: 3. + {len(new_chunk_frac)} digits")
    else:
        file_content = new_chunk_frac

    out_file = DATA_DIR / f"pi_{start:08d}-{end:08d}.txt"
    out_file.write_text(file_content)
    
    INDEX_FILE.write_text(json.dumps({"total_digits": total+CHUNK}, indent=2))
    
    update_progress_cli(
        total_digits=total+CHUNK,
        status="computed",
        last_file=str(out_file.name),
        total_files=len(list(DATA_DIR.glob("pi_*.txt")))
    )
    cli_log(f"Saved: {out_file.name} -> preview: {file_content[:10]}... ({len(file_content):,} chars)")

if __name__ == "__main__":
    main()
