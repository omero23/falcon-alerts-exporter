import os
import json
import datetime
import logging
from time import sleep

import requests
from elasticsearch import Elasticsearch, helpers

# ================== Ayarlar ==================
# Tenant bölgenize göre güncelleyin (örn: https://api.eu-1.crowdstrike.com)
BASE_URL   = os.getenv("FALCON_BASE_URL", "AdressInfo")
CLIENT_ID  = os.getenv("FALCON_CLIENT_ID",  "CLIENT_ID")
CLIENT_SEC = os.getenv("FALCON_CLIENT_SECRET", "CLIENT_SECRET")

ES_HOST  = os.getenv("ES_HOST",  "http://ELK_IP_ADRESS:9200")
ES_INDEX = os.getenv("ES_INDEX", "falcon-alerts")  # Varsayılan; aşağıda günlük index ile override ediyoruz
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "30"))
PAGE_LIMIT = int(os.getenv("PAGE_LIMIT", "500"))  # combined için 500 iyi bir değer

# ================== Logging ==================
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger("falcon-alerts")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "FalconAlertsExporter/1.0"})
TIMEOUT = 30

def request_retry(method, url, **kwargs):
    """429/5xx için basit retry. 4xx'lerde body'yi log'lar."""
    for attempt in range(5):
        resp = SESSION.request(method, url, timeout=TIMEOUT, **kwargs)
        if resp.status_code in (429, 500, 502, 503, 504):
            wait = min(2 ** attempt, 30)
            log.warning(f"{resp.status_code} - retry {attempt+1}/5 in {wait}s: {url}")
            sleep(wait)
            continue
        if resp.status_code >= 400:
            log.error(f"HTTP {resp.status_code} for {url}\n{resp.text[:2000]}")
        resp.raise_for_status()
        return resp
    raise RuntimeError("Max retries reached")


def get_token():
    url = f"{BASE_URL}/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SEC,
        "grant_type": "client_credentials",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = request_retry("POST", url, data=data, headers=headers)
    tok = r.json()["access_token"]
    log.info("API token alındı.")
    return tok


def build_working_fql(token, start_iso, end_iso):
    """
    Hangi FQL varyantının kabul edildiğini hızlıca bulur.
    GET /alerts/queries/alerts/v1 ile 1'lik bir smoke test yapar.
    """
    url = f"{BASE_URL}/alerts/queries/alerts/v1"
    headers = {"Authorization": f"Bearer {token}"}

    candidates = [
        # updated_timestamp - tırnaklı
        f"updated_timestamp:>='{start_iso}'+updated_timestamp:<='{end_iso}'",
        # created_timestamp - tırnaklı
        f"created_timestamp:>='{start_iso}'+created_timestamp:<='{end_iso}'",
        # updated_timestamp - tırnaksız
        f"updated_timestamp:>={start_iso}+updated_timestamp:<={end_iso}",
        # created_timestamp - tırnaksız
        f"created_timestamp:>={start_iso}+created_timestamp:<={end_iso}",
    ]

    last_err = None
    for fql in candidates:
        try:
            resp = SESSION.get(url, headers=headers, params={"limit": 1, "filter": fql}, timeout=TIMEOUT)
            if resp.status_code == 200 and "resources" in resp.json():
                log.info(f"FQL doğrulandı: {fql}")
                return fql
            else:
                last_err = f"status={resp.status_code} body={resp.text[:400]}"
        except Exception as e:
            last_err = str(e)

    raise RuntimeError(f"Hiçbir FQL varyantı kabul edilmedi. Son hata: {last_err}")


def fetch_alert_details_combined(token, start_iso, end_iso, fql=None):
    """
    Büyük hacim için önerilen yol:
    POST /alerts/combined/alerts/v1  (after token ile sayfalama)
    """
    if not fql:
        fql = build_working_fql(token, start_iso, end_iso)

    url = f"{BASE_URL}/alerts/combined/alerts/v1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    all_items, after, page = [], None, 0
    while True:
        body = {"filter": fql, "limit": PAGE_LIMIT}
        if after:
            body["after"] = after

        r = request_retry("POST", url, headers=headers, json=body)
        data = r.json()
        resources = data.get("resources", []) or []
        all_items.extend(resources)
        page += 1
        log.info(f"combined page {page}: got={len(resources)} total_sofar={len(all_items)}")

        after = data.get("meta", {}).get("pagination", {}).get("after")
        if not after:
            break
    return all_items


def upload_to_elasticsearch(file_path, es_host=ES_HOST, index_name=ES_INDEX):
    es = Elasticsearch([es_host])
    if not es.ping():
        log.error("Elasticsearch'e bağlanılamadı.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def gen():
        for doc in data:
            yield {"_index": index_name, "_source": doc}

    success, failed = helpers.bulk(es, gen(), stats_only=True)
    log.info(f"Elasticsearch yükleme bitti. Başarılı: {success}, Başarısız: {failed}")


# === YENİ: günlük index adı üretici ===
def make_daily_index(prefix="falcon-alerts", dt=None):
    if dt is None:
        dt = datetime.datetime.now(datetime.UTC)
    # Örn: falcon-alerts-2025.10.08
    return f"{prefix}-{dt.strftime('%Y.%m.%d')}"


if __name__ == "_main_":
    end_time = datetime.datetime.now(datetime.UTC)
    start_time = end_time - datetime.timedelta(days=LOOKBACK_DAYS)
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    log.info(f"Alarm aralığı: {start_str} - {end_str}")

    token = get_token()

    alerts = fetch_alert_details_combined(token, start_str, end_str)

    json_path = "alerts.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)
    log.info(f"{len(alerts)} alert detayı '{json_path}' dosyasına kaydedildi.")

    # === YENİ: günlük index adıyla yükle ===
    index_prefix = os.getenv("ES_INDEX_PREFIX", "falcon-alerts")  # istersen env ile değiştir
    daily_index = make_daily_index(prefix=index_prefix, dt=end_time)
    log.info(f"Veriler Elasticsearch'e yükleniyor... index='{daily_index}'")
    upload_to_elasticsearch(json_path, es_host=ES_HOST, index_name=daily_index)
