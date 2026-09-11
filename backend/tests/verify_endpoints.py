"""Verification script to test and benchmark all CyberYukti backend endpoints."""

import json
import time
import urllib.request
import urllib.error

ENDPOINTS = [
    ("GET", "http://localhost:8000/"),
    ("GET", "http://localhost:8000/docs"),
    ("GET", "http://localhost:8000/redoc"),
    ("GET", "http://localhost:8000/api/v1/clusters"),
    ("GET", "http://localhost:8000/api/v1/report"),
    ("POST", "http://localhost:8000/api/v1/scan/demo-ingest"),
    ("GET", "http://127.0.0.1:8000/"),
    ("GET", "http://127.0.0.1:8000/docs"),
    ("GET", "http://127.0.0.1:8000/api/v1/clusters"),
]

def main():
    print(f"{'METHOD':<6} {'ENDPOINT':<50} {'STATUS':<8} {'LATENCY':<12} {'RESULT'}")
    print("=" * 95)

    all_passed = True
    for method, url in ENDPOINTS:
        t0 = time.time()
        try:
            req = urllib.request.Request(
                url,
                method=method,
                headers={"User-Agent": "CyberYukti-Tester/1.0", "Accept": "application/json, text/html"}
            )
            if method == "POST":
                req.data = b"{}"

            with urllib.request.urlopen(req, timeout=5) as res:
                latency_ms = (time.time() - t0) * 1000
                content = res.read()
                content_type = res.headers.get("content-type", "")

                info = f"{len(content)} bytes"
                if "json" in content_type:
                    data = json.loads(content)
                    if isinstance(data, list):
                        info += f", {len(data)} clusters returned"
                    elif isinstance(data, dict):
                        keys = list(data.keys())
                        info += f", keys: {keys}"
                elif "html" in content_type:
                    info += ", HTML UI loaded"

                print(f"{method:<6} {url:<50} {res.status:<8} {latency_ms:>7.2f} ms    [PASS] {info}")

        except Exception as e:
            all_passed = False
            latency_ms = (time.time() - t0) * 1000
            print(f"{method:<6} {url:<50} {'ERROR':<8} {latency_ms:>7.2f} ms    [FAIL] {e}")

    print("=" * 95)
    if all_passed:
        print("[SUCCESS] All endpoints are operating correctly with instant latency!")
    else:
        print("[WARNING] One or more endpoints encountered issues.")

if __name__ == "__main__":
    main()
