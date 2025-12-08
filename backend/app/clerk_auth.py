"""
Clerk Authentication Integration for Backend API

This module provides JWT token validation for Clerk authentication.
Clerk issues JWTs that we can verify using their public keys.
"""
import os
import httpx
from fastapi import Request, HTTPException, status
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions


async def get_current_clerk_user(request: Request) -> dict:
    """
    FastAPI dependency that validates Clerk JWT token and returns user info.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        dict with user_id and session information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get Clerk SDK client
        secret_key = os.getenv('CLERK_SECRET_KEY')
        if not secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Clerk secret key not configured"
            )
        
        sdk = Clerk(bearer_auth=secret_key)
        
        # Convert FastAPI Request to httpx.Request for Clerk SDK
        httpx_request = httpx.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers)
        )
        
        # Authenticate with Clerk
        request_state = sdk.authenticate_request(
            httpx_request,
            AuthenticateRequestOptions(
                authorized_parties=['http://localhost:4321', 'https://youtharoot.app']
            )
        )
        
        # Check if user is signed in
        if not request_state.is_signed_in:
            print(f"🔐 Authentication failed: user not signed in")
            print("Reason:", request_state.reason)
            print("Token claims (unverified):", request_state.payload)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated" + (f": {request_state.reason}" if request_state.reason else "")
            )
        
        # Extract user ID from the JWT payload
        # The payload contains the token claims including 'sub' (subject/user_id)
        payload = request_state.payload
        user_id = payload.get('sub')
        session_id = payload.get('sid')
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session: missing user ID"
            )
        
        print(f"🔐 Authentication successful: user_id={user_id}, session_id={session_id}")
        
        return {
            "user_id": user_id,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🔐 Authentication error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )