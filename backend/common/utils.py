"""Common utilities and helpers"""
from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any
import httpx
from .security import decode_token


async def verify_internal_token(token: str, expected_token: str) -> bool:
    """Verify internal service token"""
    return token == expected_token


async def get_current_user_from_token(token: str) -> Dict[str, Any]:
    """Extract user info from access token"""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def verify_user_type(payload: Dict[str, Any], allowed_types: list) -> bool:
    """Verify user has required type"""
    user_type = payload.get("user_type")
    return user_type in allowed_types


def get_request_headers(request: Request) -> Dict[str, str]:
    """Extract headers from FastAPI request"""
    return {
        "x-forwarded-for": request.headers.get("x-forwarded-for", ""),
        "x-real-ip": request.headers.get("x-real-ip", request.client.host if request.client else ""),
    }


async def call_service_api(
    url: str,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Call another microservice API"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=json_data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=json_data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service communication error: {str(e)}"
            )
