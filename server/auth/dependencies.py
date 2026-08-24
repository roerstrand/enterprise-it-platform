from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from auth.security import decode_access_token, ROLES

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/demo/api/login")

class CurrentUser:
    def __init__(self, id: int, email: str, role: str):
        self.id = id
        self.email = email
        self.role = role

    # Så att @router.get("/api/me") kan returnera objektet direkt som JSON utan egen mappning
    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "role": self.role}

def get_current_user(token: str = Depends(oauth2_schema)) -> CurrentUser:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    role = payload.get("role")
    if role not in ROLES:
        # Gamla tokens utfärdade innan roll fanns i JWT-payloaden - tvinga omlogin istället för att gissa roll
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing role claim, please log in again")
    sub = payload.get("sub")
    email = payload.get("email")
    # .get() istället för indexering - en giltigt signerad token utan sub/email ska ge samma
    # rena 401 som ovan, inte en okontrollerad KeyError (500) längre ner i anropskedjan
    if sub is None or email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing required claims, please log in again")
    return CurrentUser(id=int(sub), email=email, role=role)

def require_roles(*allowed_roles: str):
    # Factory: Depends(require_roles("admin", "operator")) - används per endpoint för att begränsa vilka roller som får mutera
    def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{user.role}' is not permitted to perform this action")
        return user
    return _check
