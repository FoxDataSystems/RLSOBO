"""
Authenticatie en autorisatie
"""
from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from jose import JWTError, jwt
from app.config import settings


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Haal huidige gebruiker op uit OAuth token
    Voor demo doeleinden kan dit ook een mock token zijn
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geen autorisatie token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Haal token uit Authorization header
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ongeldig autorisatie schema"
            )
        
        # Decode JWT token (voor Azure AD tokens)
        # In productie: gebruik Azure AD token validation
        decoded_token = jwt.decode(
            token,
            options={"verify_signature": False}  # Voor demo, in productie wel valideren!
        )
        
        return {
            "oid": decoded_token.get("oid"),  # Azure AD Object ID
            "name": decoded_token.get("name"),
            "email": decoded_token.get("email") or decoded_token.get("preferred_username"),
            "roles": decoded_token.get("roles", [])
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ongeldig token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authenticatie fout: {str(e)}"
        )


def get_user_from_token(token: str) -> dict:
    """Helper functie om gebruiker uit token te halen"""
    try:
        decoded = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        return {
            "oid": decoded.get("oid"),
            "name": decoded.get("name"),
            "email": decoded.get("email") or decoded.get("preferred_username")
        }
    except Exception:
        return {}

