
# falcon-alerts-exporter
Python script for exporting CrowdStrike Falcon alerts and indexing into Elasticsearch (SOF-ELK)
# 🦅 Falcon Alerts Exporter

**Falcon Alerts Exporter**, CrowdStrike Falcon platformunda oluşan tespit (detection) verilerini **otomatik olarak dışa aktararak (export)** uzun süreli saklama ve analiz için **Elasticsearch (SOF-ELK)** ortamına aktaran bir Python betiğidir.

---

## 🚀 Purpose
CrowdStrike Falcon ortamında alarm (detection alert) kayıtları varsayılan olarak **90 gün** saklanmaktadır.  
Bu script, geçmiş veriye erişim ihtiyacını karşılamak amacıyla geliştirilmiş olup, **son 30 günlük** veriyi otomatik olarak çekip Elasticsearch’e yükler.  
Böylece SOC/MDR ekipleri geçmiş olaylar üzerinde **threat hunting, korelasyon ve trend analizi** çalışmalarını uzun dönemli olarak sürdürebilir.

---

## ⚙️ How It Works
Script aşağıdaki adımları otomatik olarak gerçekleştirir:

1. **OAuth2 token** ile CrowdStrike API’ye güvenli bağlantı kurar.  
2. Son 30 güne ait veriyi `LOOKBACK_DAYS = 30` parametresiyle alır.  
3. API isteğini optimize eder, gerekirse `combined/alerts/v1` endpoint’i üzerinden sayfalama (pagination) yapar.  
4. Çekilen alert’leri `alerts.json` dosyasına kaydeder.  
5. Veriyi Elasticsearch ortamına yükler. Günlük index formatı:

6. Örneğin: `falcon-alerts-2025.10.16`

---

## 🧩 Configuration
Aşağıdaki ortam değişkenleri (environment variables) ile yapılandırma yapılabilir:

```bash
export FALCON_BASE_URL="https://api.us-2.crowdstrike.com"
export FALCON_CLIENT_ID="your_client_id"
export FALCON_CLIENT_SECRET="your_client_secret"
export ES_HOST="http://your_elasticsearch:9200"
export ES_INDEX="falcon-alerts"
export LOOKBACK_DAYS=30

## 🧠 Technical Notes
	•	API Endpoint: /alerts/combined/alerts/v1
	•	Index Format: Günlük (timestamp tabanlı)
	•	Retry Mekanizması: 429 / 5xx hata kodları için exponential backoff
	•	Uygulama Dili: Python 3
	•	Bağımlılıklar: requests, elasticsearch

💡 Development & Support

Bu proje, ChatGPT (OpenAI GPT-5) desteğiyle geliştirilmiştir.
Kodun yapısı, hata toleransı, Elasticsearch indexleme ve 30 günlük veri aralığı konfigürasyonu birlikte tasarlanmıştır.

🧾 Example Output

INFO:falcon-alerts:API token alındı.
INFO:falcon-alerts:combined page 1: got=500 total_sofar=500
INFO:falcon-alerts:combined page 2: got=312 total_sofar=812
INFO:falcon-alerts:Veriler Elasticsearch'e yükleniyor... index='falcon-alerts-2025.10.16'
INFO:falcon-alerts:Elasticsearch yükleme bitti. Başarılı: 812, Başarısız: 0

🧑‍💻 Author

Ömer Faruk Özer
Security Operations & DFIR Engineer
🔗 LinkedIn
📧 ofaruk.ozr@gmail.com
