"""Capture regulator evidence serially; credentials never enter saved URLs or logs."""

import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlparse

from dotenv import dotenv_values
import httpx

HERE = Path(__file__).resolve().parent
DIGEST = HERE.parents[3] / "filing-digest"
ALLOWED = {"dart.fss.or.kr", "opendart.fss.or.kr", "www.sec.gov", "data.sec.gov"}


def main():
    config = dotenv_values(DIGEST / "backend/.env")
    key = config.get("DART_API_KEY")
    user_agent = config.get("SEC_USER_AGENT")
    corpus = json.loads((HERE / "corpus.json").read_text())["data"]
    companies = {c["id"]: c for c in corpus["companies"]}
    folder = HERE / "sources"
    folder.mkdir(exist_ok=True)
    record_path = HERE / "source-checks.json"
    records = json.loads(record_path.read_text()) if record_path.exists() else []
    for record in records:
        if record.get("path", "").endswith(".html"):
            body = (HERE / record["path"]).read_text(errors="replace")
            if re.search(r"<title>\s*거부\s*</title>", body):
                record["status"] = "denial_page_http_200"
        if record.get("bytes", 0) > 200000 and record.get("path", "").endswith((".html", ".json")):
            path = HERE / record["path"]
            compressed = gzip.compress(path.read_bytes(), mtime=0)
            path.with_suffix(path.suffix + ".gz").write_bytes(compressed)
            path.unlink()
            record["path"] += ".gz"
            record["storage_encoding"] = "gzip; sha256 and bytes refer to decompressed original response"
            record["stored_bytes"] = len(compressed)
    record_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")

    def capture(name, url, params=None, authenticated=False):
        if any(record["name"] == name for record in records):
            return
        assert urlparse(url).hostname in ALLOWED
        safe_params = params or {}
        record = {"name": name, "url": url, "parameters": safe_params,
                  "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        if authenticated and not key:
            record["status"] = "missing_dart_key"
        elif urlparse(url).hostname.endswith("sec.gov") and (not user_agent or "example.com" in user_agent):
            record["status"] = "missing_sec_contact_user_agent"
        else:
            headers = {"User-Agent": user_agent} if "sec.gov" in urlparse(url).hostname else {}
            request_params = dict(safe_params)
            if authenticated:
                assert urlparse(url).hostname == "opendart.fss.or.kr"
                request_params["crtfc_key"] = key
            try:
                with httpx.Client(trust_env=False, timeout=30, follow_redirects=False) as client:
                    response = client.get(url, params=request_params, headers=headers)
                record["http_status"] = response.status_code
                record["content_type"] = response.headers.get("content-type")
                record["status"] = "captured" if response.status_code == 200 else "http_error"
                body = response.content
                if key and key.encode() in body:
                    raise ValueError("Credential unexpectedly present in response; not saved")
                suffix = ".zip" if body.startswith(b"PK\x03\x04") else ".json" if "json" in (record["content_type"] or "") else ".html"
                filename = name + suffix
                (folder / filename).write_bytes(body)
                record.update(path="sources/" + filename, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
                if suffix == ".html" and re.search(r"<title>\s*거부\s*</title>", response.text):
                    record["status"] = "denial_page_http_200"
                if filename.endswith(".json") and response.status_code == 200:
                    payload = response.json()
                    record["api_status"] = payload.get("status")
                    if authenticated and record["api_status"] != "000":
                        record["status"] = "api_error"
                if len(body) > 200000 and suffix != ".zip":
                    compressed = gzip.compress(body, mtime=0)
                    (folder / (filename + ".gz")).write_bytes(compressed)
                    (folder / filename).unlink()
                    record["path"] += ".gz"
                    record["storage_encoding"] = "gzip; sha256 and bytes refer to decompressed original response"
                    record["stored_bytes"] = len(compressed)
            except (httpx.HTTPError, ValueError) as error:
                record["status"] = type(error).__name__
            time.sleep(0.3)
        records.append(record)
        (HERE / "source-checks.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
        print(name, record["status"], record.get("http_status", ""), record.get("api_status", ""), flush=True)

    for filing in corpus["filings"]:
        identity = filing["rcept_no"] or filing["sec_accession_no"]
        capture("filing-" + identity, filing["url"])
    dart_requests = {(companies[f["company_id"]]["dart_corp_code"], f["period"][:4])
                     for f in corpus["filings"] if f["source"] == "dart"}
    dart_requests.add(("00266961", "2023"))
    for corp, year in sorted(dart_requests):
        capture(f"dart-financials-{corp}-{year}", "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
                {"corp_code": corp, "bsns_year": year, "reprt_code": "11011", "fs_div": "CFS"}, True)
    for company in corpus["companies"]:
        if company["source"] == "sec":
            cik = company["sec_cik"]
            capture("sec-companyfacts-" + cik, f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
    receipts = set()
    for source in folder.glob("dart-financials-*.json"):
        receipts.update(row["rcept_no"] for row in json.loads(source.read_text()).get("list", []))
    for receipt in sorted(receipts):
        capture("dart-document-" + receipt, "https://opendart.fss.or.kr/api/document.xml",
                {"rcept_no": receipt}, True)
    for corp, receipt in [("00126380", "20240312000736"), ("00266961", "20240318000844")]:
        capture("dart-list-" + receipt, "https://opendart.fss.or.kr/api/list.json",
                {"corp_code": corp, "bgn_de": receipt[:8], "end_de": receipt[:8], "page_count": "100"}, True)


if __name__ == "__main__":
    main()
