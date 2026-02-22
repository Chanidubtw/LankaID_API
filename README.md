# 🇱🇰 LankaID

A production-ready REST API to validate Sri Lankan National Identity Card (NIC) numbers.
Supports both old (9-digit + V/X) and new (12-digit) formats.

---

## 🚀 Quick Start

### 1. Clone / download this project

```bash
cd lanka-nic-api
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn main:app --reload
```

The API is now running at: **http://localhost:8000**

Interactive docs at: **http://localhost:8000/docs**

---

## 📖 API Reference

### Register for an API Key

```http
POST /keys/register
Content-Type: application/json

{
  "name": "Kamal Perera",
  "email": "kamal@example.lk"
}
```

**Response:**
```json
{
  "message": "API key created successfully.",
  "api_key": "lnic_xxxxxxxxxxxxxxxxxxxx",
  "plan": "free",
  "monthly_limit": 1000
}
```

---

### Validate a NIC

```http
POST /validate
X-API-Key: lnic_your_key_here
Content-Type: application/json

{
  "nic": "990123456V"
}
```

**Response:**
```json
{
  "valid": true,
  "nic": "990123456V",
  "format": "old",
  "date_of_birth": "1999-01-23",
  "gender": "Male",
  "age": 25
}
```

---

### Verify NIC against a Date of Birth

```http
POST /verify
X-API-Key: lnic_your_key_here
Content-Type: application/json

{
  "nic": "990123456V",
  "date_of_birth": "1999-01-23"
}
```

**Response:**
```json
{
  "nic": "990123456V",
  "format": "old",
  "match": true,
  "nic_date_of_birth": "1999-01-23",
  "provided_date_of_birth": "1999-01-23",
  "gender": "Male",
  "age": 25
}
```

---

### Check API Key Status

```http
GET /keys/status
X-API-Key: lnic_your_key_here
```

---

## 🗂 NIC Format Reference

| Format | Example | Year Range |
|--------|---------|------------|
| Old (10 chars) | `990123456V` | 1900–1999 |
| New (12 digits) | `199901230123` | Any year |

- **Day of year 1–366** → Male
- **Day of year 501–866** → Female (500 is subtracted to get actual day)

---

## 📁 Project Structure

```
lanka-nic-api/
├── main.py           # FastAPI app, routes, auth
├── nic_validator.py  # Core NIC parsing logic
├── database.py       # SQLite database helpers
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── README.md
```

---

## 🌐 Deploying to Production

### Option A: Railway (easiest, free tier available)
1. Push this project to a GitHub repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option B: DigitalOcean / Any VPS
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Use **Nginx** as a reverse proxy and **systemd** to keep it running.

---

## 📄 License

MIT — free to use for personal and commercial projects.
