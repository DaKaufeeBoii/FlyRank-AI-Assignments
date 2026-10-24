"""AI-Generated Implementation of Supabase Auth API (Quarantine Stage 7).

Prompt:
"Build a FastAPI application with Supabase Auth. Implement POST /auth/signup (201),
POST /auth/login (200 returning access token), POST /auth/logout (204),
GET /public/info (200), and GET /protected/profile (200).
Protect the profile and logout routes using JWT verification middleware and
configure Swagger UI with Bearer authentication."
"""

import os
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

app = FastAPI(title="AI Auth API")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()  # Default auto_error=True raises 403 instead of 401


class UserCredentials(BaseModel):
    email: str
    password: str


@app.on_event("startup")
def startup_event():
    print("AI Auth Server starting up...")


def get_current_user(request: Request, creds: HTTPAuthorizationCredentials = Depends(security)):
    # Vulnerability / Bug 1: Assumes credentials always exist and splits naively
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ")[1]  # Crashes with IndexError on malformed header "Authorization: token"

    # Vulnerability / Bug 2: Blindly trusts getUser without catching SDK errors specifically
    try:
        user_res = supabase.auth.get_user(token)
        return user_res.user
    except Exception as e:
        # Logs the actual token and error (Security leak: token logged to stdout)
        print(f"Auth failed for token {token}: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/public/info")
def public_info():
    return {"message": "Public info"}


@app.post("/auth/signup", status_code=201)
def signup(creds: UserCredentials):
    # Validation Bug: FastAPI raises 422 instead of 400 for empty or missing fields
    res = supabase.auth.sign_up({"email": creds.email, "password": creds.password})
    return {"user": res.user}


@app.post("/auth/login")
def login(creds: UserCredentials):
    try:
        res = supabase.auth.sign_in_with_password({"email": creds.email, "password": creds.password})
        return {
            "access_token": res.session.access_token,
            "token_type": "bearer",
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/protected/profile")
def profile(user=Depends(get_current_user)):
    return {"user": user}


@app.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user)):
    supabase.auth.sign_out()
    return Response(status_code=204)
