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
    print(f"\n[CLI PROGRESS] {kw}")

# --- ここから超高速 Binary Splitting ---
C3_OVER_24 = 545140134 * 3

def bs(a, b):
    """binary splitting [a,b) の (Pab, Qab, Rab) を返す"""
    if b - a == 1:
        if a == 0:
            Pab = Qab = gmpy2.mpz(1)
            Rab = gmpy2.mpz(13591409)
        else:
            Pab = gmpy2.mpz((6*a-5)*(2*a-1)*(6*a-1))
            Qab = gmpy2.mpz(a*a*a * 262537412640768000)
            Rab = gmpy2.mpz(Pab * (13591409 + C3_OVER_24 * a))
            Pab = -Pab
    else:
        m = (a + b) // 2
        Pam, Qam, Ram = bs(a, m)
        Pmb, Qmb, Rmb = bs(m, b)
        Pab = Pam * Pmb
        Qab = Qam * Qmb
        Rab = Qam * Rmb + Pam * Ram
    return Pab, Qab, Rab

def compute_pi_digits(n):
    """n桁(小数点以下)のpiを返す - Binary Splittingで数秒"""
    cli_log(f"Start FAST Chudnovsky BS for {n:,} digits")
    gmpy2.get_context().precision = int(n * 3.32192809489 + 100)
    
    digits_per_term = 14.181647462
    N = int(n / digits_per_term) + 5
    
    t0 = time.time()
    _, Q, R = bs(0, N)
    cli_log(f"BS done in {time.time()-t0:.2f}s (N={N})")

    # pi = Q * 426880 * sqrt(10005) / R
    sqrt_10005 = gmpy2.sqrt(gmpy2.mpz(10005))
    pi = Q * 426880 * sqrt_10005 / R

    # 文字列化
    # gmpy2の精度だとstr(pi)で足りないので、mpfr->stringを工夫
    s = gmpy2.mpfr(pi)
    # 整数部3を除いた小数部だけ欲しい
    frac = str(s).split('.')[1]
    # 桁数足りない場合は0埋め
    frac = (frac + '0'*n)[:n]
    
    # gmpy2のstrが丸めで桁数足りない時の保険
    if len(frac) < n:
        # 追加計算
        gmpy2.get_context().precision *= 2
        s = gmpy2.mpfr(pi)
        frac = str(s).split('.')[1][:n]

    cli_log(f"Computed {len(frac)} digits in {time.time()-t0:.2f}s")
    return frac
# --- 高速化ここまで ---

def main():
    DATA_DIR.mkdir(exist_ok=True)
    total = json.loads(INDEX_FILE.read_text()).get("total_digits", 0) if INDEX_FILE.exists() else 0
    
    start = total
    end = total + CHUNK - 1
    
    cli_log(f"=== Pi Calculator FAST (0-index, frac only) ===")
    cli_log(f"Current total: {total:,} -> Next: {start:,}-{end:,}")

    update_progress_cli(
        total_digits=total,
        status="start_computing",
        next_range=f"{start}-{end}"
    )

    full_frac = compute_pi_digits(total + CHUNK)
    new_chunk = full_frac[start:start+CHUNK]

    out_file = DATA_DIR / f"pi_{start:08d}-{end:08d}.txt"
    out_file.write_text(new_chunk)
    
    INDEX_FILE.write_text(json.dumps({"total_digits": total+CHUNK}, indent=2))
    
    update_progress_cli(
        total_digits=total+CHUNK,
        status="computed",
        last_file=str(out_file.name),
        total_files=len(list(DATA_DIR.glob("pi_*.txt")))
    )
    cli_log(f"Saved: {out_file.name} preview={new_chunk[:20]}...")

if __name__ == "__main__":
    main()
