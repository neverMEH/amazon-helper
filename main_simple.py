"""Simplified FastAPI application for testing OAuth flow"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
import secrets

# Load environment variables
load_dotenv()

app = FastAPI(title="AMC Manager - Simple OAuth Test")

# Simple in-memory store for testing
tokens_store = {}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AMC Manager Simple OAuth Test",
        "endpoints": {
            "login": "/api/auth/login",
            "callback": "/api/auth/callback",
            "docs": "/docs"
        }
    }

@app.get("/api/auth/login")
async def login():
    """Initiate OAuth login flow"""
    client_id = os.getenv('AMAZON_CLIENT_ID')
    redirect_uri = os.getenv('AMAZON_REDIRECT_URI')
    scope = os.getenv('AMAZON_SCOPE')
    
    if not all([client_id, redirect_uri, scope]):
        raise HTTPException(status_code=500, detail="Missing OAuth configuration")
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Build authorization URL
    base_url = "https://www.amazon.com/ap/oa"
    params = {
        'client_id': client_id,
        'scope': scope,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'state': state
    }
    
    param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    auth_url = f"{base_url}?{param_string}"
    
    return {
        "message": "Click the authorization URL to login with Amazon",
        "auth_url": auth_url,
        "state": state
    }

@app.get("/api/auth/callback")
async def auth_callback(
    code: str = Query(..., description="Authorization code from Amazon"),
    state: str = Query(None, description="State parameter for CSRF protection")
):
    """Handle OAuth callback from Amazon"""
    
    # In a real app, you would:
    # 1. Verify the state parameter
    # 2. Exchange the code for tokens
    # 3. Store the tokens securely
    # 4. Create a session for the user
    
    # For now, let's just show that we received the callback
    return JSONResponse({
        "message": "OAuth callback received successfully!",
        "code": code[:10] + "..." if code else None,
        "state": state[:10] + "..." if state else None,
        "next_steps": [
            "In a real application, this code would be exchanged for access tokens",
            "The tokens would be stored securely",
            "User would be logged in and redirected to the dashboard"
        ]
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Starting AMC Manager Simple OAuth Test Server")
    print("="*50)
    print(f"\nServer running at: http://localhost:8000")
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"OAuth Login: http://localhost:8000/api/auth/login")
    print("\nPress CTRL+C to stop the server")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)