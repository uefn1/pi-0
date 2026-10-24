import json, datetime
from pathlib import Path
import gmpy2

CHUNK = 100_000
DATA_DIR = Path("pi_data")
INDEX_FILE = DATA_DIR / "index.json"
PROGRESS_FILE = DATA_DIR / "progress.json"

def update_progress(**kw):
    DATA_DIR.mkdir(exist_ok=True)
    data = json.loads(PROGRESS_FILE.read_text()) if PROGRESS_FILE.exists() else {}
    data.update(kw)
    data["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    PROGRESS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[PROGRESS] {data}")

def compute_pi_digits(n):
    gmpy2.get_context().precision = int(n * 3.5 + 100)
    C = 426880 * gmpy2.sqrt(gmpy2.mpz(10005))
    M, L, X, K, S = gmpy2.mpz(1), gmpy2.mpz(13591409), gmpy2.mpz(1), gmpy2.mpz(6), gmpy2.mpz(13591409)
    for i in range(1, n // 14 + 10):
        if i % 200 == 0:
            update_progress(status="computing", iter=f"{i}/{n//14}")
        M = (K**3 - 16*K) * M // (i**3)
        L += 545140134
        X *= -262537412640768000
        S += M * L / X
        K += 12
    pi = C / S
    return (str(pi).split('.')[1] + '0'*n)[:n]

def main():
    DATA_DIR.mkdir(exist_ok=True)
    total = json.loads(INDEX_FILE.read_text()).get("total_digits", 0) if INDEX_FILE.exists() else 0
    
    update_progress(
        total_digits=total,
        status="start_computing",
        next_range=f"{total+1}-{total+CHUNK}",
        total_files=len(list(DATA_DIR.glob("pi_*.txt")))
    )

    full = compute_pi_digits(total + CHUNK)
    new_chunk = full[total:total+CHUNK]

    (DATA_DIR / f"pi_{total+1:08d}-{total+CHUNK:08d}.txt").write_text(new_chunk)
    INDEX_FILE.write_text(json.dumps({"total_digits": total+CHUNK}, indent=2))
    
    # ★プロセス終了前に必ず更新される進捗
    update_progress(
        total_digits=total+CHUNK,
        status="computed",
        last_file=f"pi_{total+1:08d}-{total+CHUNK:08d}.txt",
        total_files=len(list(DATA_DIR.glob("pi_*.txt")))
    )

if __name__ == "__main__":
    main()
