import os
import secrets
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import init_db, get_api_key_record, increment_request_count, log_request, create_api_key_record
from nic_validator import parse_nic, verify_nic_with_dob, get_gender_from_nic

FREE_TIER_LIMIT = 200

# ─── App Setup ────────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Lanka NIC API",
    description="""
## 🇱🇰 Sri Lankan NIC Validation API

Validate and extract information from Sri Lankan National Identity Card (NIC) numbers.

### Features
- ✅ Supports **old format** (9 digits + V/X) and **new format** (12 digits)
- 📅 Extracts **date of birth** and **gender** from the NIC
- 🔐 Verify if a NIC matches a provided date of birth
- 🚀 Simple REST API with API key authentication

### Getting Started
1. Register for a free API key using `POST /keys/register`
2. Include your key in every request header: `X-API-Key: your_key_here`
3. Start validating NICs!

### Rate Limits
- **Free plan**: 1,000 requests/month
- Contact us to upgrade your plan.
    """,
    version="1.0.0",
    contact={
        "name": "Lanka NIC API",
        "email": "support@lankanicapi.lk",
    },
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Init DB on startup ───────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()

# ─── Models ───────────────────────────────────────────────────────────────────

class ValidateRequest(BaseModel):
    nic: str

    class Config:
        json_schema_extra = {
            "example": {"nic": "990123456V"}
        }


class VerifyRequest(BaseModel):
    nic: str
    date_of_birth: str  # YYYY-MM-DD

    class Config:
        json_schema_extra = {
            "example": {
                "nic": "990123456V",
                "date_of_birth": "1999-01-23"
            }
        }


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Kamal Perera",
                "email": "kamal@example.lk"
            }
        }


# ─── Auth Helper ─────────────────────────────────────────────────────────────

def authenticate(x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key. Include 'X-API-Key' in your request headers.")

    record = get_api_key_record(x_api_key)

    if not record:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key.")

    if record["request_count"] >= record["monthly_limit"]:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly request limit of {record['monthly_limit']} reached. Please upgrade your plan."
        )

    increment_request_count(x_api_key)
    return record


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["General"], include_in_schema=False)
def root():
    return FileResponse("index.html")


@app.get("/dashboard", tags=["General"], include_in_schema=False)
def dashboard():
    return FileResponse("dashboard.html")


@app.get("/health", tags=["General"])
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/validate", tags=["NIC"])
@limiter.limit("60/minute")
def validate_nic(
    request: Request,
    body: ValidateRequest,
    api_key_record=Depends(authenticate)
):
    """
    **Validate a Sri Lankan NIC number.**

    Accepts both old format (e.g. `990123456V`) and new format (e.g. `199901230123`).

    Returns:
    - Whether the NIC is valid
    - Extracted date of birth
    - Gender
    - Age
    - NIC format (old/new)
    """
    result, error = parse_nic(body.nic)
    ip = get_remote_address(request)

    if error:
        log_request(api_key_record["key"], "/validate", body.nic, False, error, ip)
        return JSONResponse(status_code=422, content={"valid": False, "error": error})

    log_request(api_key_record["key"], "/validate", body.nic, True, None, ip)
    return result




@app.post("/gender", tags=["NIC"])
@limiter.limit("60/minute")
def gender_nic(
    request: Request,
    body: ValidateRequest,
    api_key_record=Depends(authenticate)
):
    """
    **Extract gender from a Sri Lankan NIC number.**

    A lightweight endpoint that returns only the gender encoded in the NIC.
    Useful when you only need gender without full DOB extraction.
    """
    result, error = get_gender_from_nic(body.nic)
    ip = get_remote_address(request)

    if error:
        log_request(api_key_record["key"], "/gender", body.nic, False, error, ip)
        return JSONResponse(status_code=422, content={"valid": False, "error": error})

    log_request(api_key_record["key"], "/gender", body.nic, True, None, ip)
    return result

@app.post("/verify", tags=["NIC"])
@limiter.limit("60/minute")
def verify_nic(
    request: Request,
    body: VerifyRequest,
    api_key_record=Depends(authenticate)
):
    """
    **Verify that a NIC matches a provided date of birth.**

    Useful for KYC — checks whether the date of birth encoded in the NIC
    matches the date of birth the user claims.

    `date_of_birth` must be in **YYYY-MM-DD** format.
    """
    result, error = verify_nic_with_dob(body.nic, body.date_of_birth)
    ip = get_remote_address(request)

    if error:
        log_request(api_key_record["key"], "/verify", body.nic, False, error, ip)
        return JSONResponse(status_code=422, content={"valid": False, "error": error})

    log_request(api_key_record["key"], "/verify", body.nic, True, None, ip)
    return result


@app.post("/keys/register", tags=["API Keys"])
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest):
    """
    **Register for a free API key.**

    Generates a new API key tied to your name and email.
    Free plan includes **200 requests/month**.
    """
    new_key = "lnic_" + secrets.token_urlsafe(32)
    success = create_api_key_record(new_key, body.name, body.email)

    if not success:
        raise HTTPException(status_code=409, detail="An account with this email may already exist. Contact support.")

    return {
        "message": "API key created successfully. Keep it safe — it won't be shown again.",
        "api_key": new_key,
        "plan": "free",
        "monthly_limit": 200,
        "usage": "Include in request headers as: X-API-Key: " + new_key
    }


@app.get("/keys/status", tags=["API Keys"])
def key_status(api_key_record=Depends(authenticate)):
    """
    **Check your API key usage and status.**
    """
    return {
        "name": api_key_record["name"],
        "email": api_key_record["email"],
        "plan": api_key_record["plan"],
        "request_count": api_key_record["request_count"],
        "monthly_limit": api_key_record["monthly_limit"],
        "remaining": api_key_record["monthly_limit"] - api_key_record["request_count"],
        "created_at": api_key_record["created_at"],
        "last_used": api_key_record["last_used"],
    }
