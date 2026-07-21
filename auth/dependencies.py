from fastapi import Depends, HTTPException, status
from fastapi.security import OAuthPasswordBearer

from auth.security import decode_access_token

oauth2_schema = OAuthPasswordBearer(tokenUrl="/demo/api/login")

def get_current_user(token: str = Depends(oauth2_schema)) -> dict:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload
