# 🦅 Falcon Alerts Exporter

**Falcon Alerts Exporter** is a Python-based automation that exports detection alerts from **CrowdStrike Falcon API** and indexes them into **Elasticsearch (SOF-ELK)** for long-term storage, visibility, and threat hunting operations.

---

## 🚀 Overview
By default, **CrowdStrike Falcon retains alert data for 90 days**, which can be limiting for SOC and MDR environments that require historical visibility.  
This script automatically collects the **last 30 days** of alert data and pushes it to Elasticsearch, enabling **multi-month or multi-year retention** for advanced threat hunting, correlation, and compliance reporting.

---

## ⚙️ Key Features
- 🔐 Secure OAuth2 authentication to CrowdStrike API  
- 📦 Fetches alerts for the last **30 days** (`LOOKBACK_DAYS = 30`)  
- 🔁 Built-in pagination and retry logic for large data sets  
- 🗂️ Exports results to `alerts.json`  
- 🧱 Automatically creates **daily indices** in Elasticsearch:

🧠 Technical Details
	•	API Endpoint: /alerts/combined/alerts/v1
	•	Data Format: JSON → Elasticsearch
	•	Index Type: Daily, timestamp-based
	•	Error Handling: Exponential retry for 429 and 5xx responses
	•	Dependencies: requests, elasticsearch
	•	Language: Python 3.x

🛠️ Usage

python3 falcon_alerts_exporter.py

🧾 Example Output

INFO:falcon-alerts:API token obtained.
INFO:falcon-alerts:combined page 1: got=500 total_sofar=500
INFO:falcon-alerts:combined page 2: got=312 total_sofar=812
INFO:falcon-alerts:Uploading data to Elasticsearch... index='falcon-alerts-2025.10.16'
INFO:falcon-alerts:Upload completed. Success: 812, Failed: 0

🤝 Development Note

The project was created with the assistance of ChatGPT (OpenAI GPT-5) to design and optimize the API integration, pagination logic, and Elasticsearch indexing flow.

👤 Author

Ömer Faruk Özer
Security Operations & DFIR Engineer
📧 ofaruk.ozr@gmail.com
🔗 LinkedIn Profile
