import urllib.request
import time
import concurrent.futures


def req(url):
    try:
        r = urllib.request.urlopen(url, timeout=5)
        return r.status
    except Exception:
        return 0


def run_phase(name, url, n, workers):
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        codes = list(ex.map(lambda _: req(url), range(n)))
    elapsed = time.time() - start
    ok = codes.count(200)
    rps = n / elapsed
    print(f"{name}: {ok}/{n} OK in {elapsed:.1f}s = {rps:.0f} RPS")
    return rps


url = "http://myapp.local/health"
rps1 = run_phase("Phase 1 (5  concurrent, 100 req)", url, 100, 5)
rps2 = run_phase("Phase 2 (30 concurrent, 300 req)", url, 300, 30)
print(f"\nRPS increase: {rps2/rps1:.1f}x at 30 concurrent vs 5")
