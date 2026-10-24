import json, argparse, datetime
from pathlib import Path
import gmpy2

CHUNK_SIZE = 100_000
DATA_DIR = Path("pi_data")
INDEX_FILE = DATA_DIR / "index.json"
PROGRESS_FILE = DATA_DIR / "progress.json"

def update_progress(**kwargs):
    DATA_DIR.mkdir(exist_ok=True)
    data = {}
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text())
    data.update(kwargs)
    data["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    PROGRESS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[PROGRESS] {data}")

def compute_pi_digits(n):
    gmpy2.get_context().precision = int(n * 3.5 + 100)
    C = 426880 * gmpy2.sqrt(gmpy2.mpz(10005))
    M = gmpy2.mpz(1)
    L = gmpy2.mpz(13591409)
    X = gmpy2.mpz(1)
    K = gmpy2.mpz(6)
    S = L
    target_iter = n // 14 + 10
    for i in range(1, target_iter):
        if i % 200 == 0:
            update_progress(status="computing", current_iter=i, target_iter=target_iter)
        M = (K**3 - 16*K) * M // (i**3)
        L += 545140134
        X *= -262537412640768000
        S += M * L / X
        K += 12
    pi = C / S
    frac = str(pi).split('.')[1]
    return (frac + '0'*n)[:n]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-digits", type=int, default=10000000)
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    total = json.loads(INDEX_FILE.read_text()).get("total_digits", 0) if INDEX_FILE.exists() else 0
    
    update_progress(
        total_digits=total,
        max_digits=args.max_digits,
        percent=round(total/args.max_digits*100, 4),
        status="start_computing",
        next_chunk=f"{total+1} - {total+CHUNK_SIZE}"
    )

    next_total = total + CHUNK_SIZE
    full_frac = compute_pi_digits(next_total)
    new_chunk = full_frac[total:next_total]

    out_file = DATA_DIR / f"pi_{total+1:08d}-{next_total:08d}.txt"
    out_file.write_text(new_chunk)
    
    INDEX_FILE.write_text(json.dumps({"total_digits": next_total}, indent=2))
    
    # 計算完了時点での進捗更新（プロセス終了前に必ず更新される）
    update_progress(
        total_digits=next_total,
        max_digits=args.max_digits,
        percent=round(next_total/args.max_digits*100, 4),
        status="computed",
        last_file=str(out_file),
        total_files=len(list(DATA_DIR.glob("pi_*.txt")))
    )

if __name__ == "__main__":
    main()
