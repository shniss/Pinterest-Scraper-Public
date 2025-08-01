from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field, validator


class PinterestCookie(BaseModel):
    name: str
    value: str
    domain: Optional[str] = None
    path: str = "/"
    expires: Optional[float] = None  # Unix seconds
    http_only: bool = False
    secure: bool = True
    same_site: str = "Lax"  # Lax | Strict | None

    # helper → playwright format
    def to_playwright(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "path": self.path,
            "httpOnly": self.http_only,
            "secure": self.secure,
            "sameSite": self.same_site,
        }
        if self.expires is not None:
            d["expires"] = int(self.expires)
        return d

    # validation: convert datetime to float if user passes datetime
    @validator("expires", pre=True)
    def _coerce_expires(cls, v):
        if isinstance(v, datetime):
            return v.replace(tzinfo=timezone.utc).timestamp()
        return v



class ProxyConfig(BaseModel):
    server: str  # host:port OR http://host:port
    username: Optional[str] = None
    password: Optional[str] = None
    # Oxylabs extras (ignored by Playwright, useful for build string)
    country: Optional[str] = None
    session_id: Optional[str] = None
    proxy_type: str = "http"  # http | https | socks5
    port: Optional[int] = None

    def to_playwright(self) -> Dict[str, str]:
        """Return kwargs for Playwright proxy param."""
        return {
            "server": (
                self.server
                if "://" in self.server
                else f"{self.proxy_type}://{self.server}"
            ),
            "username": self.username,
            "password": self.password,
        }



class PinterestAccount(BaseModel):
    username: str
    email: str
    password: str

    # persisted session blob (preferred over per‑cookie list)
    storage_state: Optional[Dict[str, Any]] = None

    # fallback legacy cookie list
    cookies: List[PinterestCookie] = Field(default_factory=list)

    proxy: Optional[ProxyConfig] = None
    user_agent: Optional[str] = None

    last_login: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def needs_login(self) -> bool:
        """Decide whether to call session.login()."""
        return self.storage_state is None

    def playwright_proxy(self) -> Optional[Dict[str, str]]:
        return self.proxy.to_playwright() if self.proxy else None

    def playwright_cookies(self) -> List[Dict[str, Any]]:
        """Convert list of PinterestCookie → Playwright cookie dicts."""
        now = datetime.utcnow().timestamp()
        return [
            c.to_playwright() for c in self.cookies if (c.expires or now + 60) > now
        ]
    
    class Config:
        orm_mode = True
        json_encoders = {datetime: lambda v: v.isoformat()}
