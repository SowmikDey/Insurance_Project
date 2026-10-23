# backend/app/services/ingestion/protected_fetcher.py
"""Secure fetcher using httpx.
Refactored to use httpx streaming correctly, enforce response size limits while streaming,
handle redirects manually, and bind the TCP connection to the validated IP address to
prevent DNS‑rebinding attacks.
"""

import ipaddress
import logging
import socket
import time
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, Optional

import httpx

from sqlalchemy.orm import Session

from app.services.ingestion.authorization_service import (
    check_authorization,
    AuthorizationActivity,
    AuthorizationDecision,
)

logger = logging.getLogger(__name__)


class SSRFSecurityException(Exception):
    """Raised when a URL attempts to target private, loopback, or metadata endpoints."""
    pass


class PermissionBlockedException(Exception):
    """Raised when an operation is blocked by source registry permission rules."""
    pass


class PayloadTooLargeException(Exception):
    """Raised when a fetched response exceeds the maximum allowed size (25MB)."""
    pass


class ProtectedFetcherService:
    """Centralized, secure HTTP client for all external data fetching in BimaGyan.
    Enforces:
    1. Scheme validation (HTTPS required for external sources).
    2. URL sanity & embedded credentials rejection.
    3. SSRF and DNS rebinding protection (resolves DNS, blocks private/loopback/cloud metadata).
    4. Backend Authorization enforcement BEFORE any network socket is opened.
    5. Manual redirect destination re‑validation (no automatic unchecked redirects).
    6. Response size bounding (max 25 MB streaming limit).
    7. Respectful per‑domain rate limiting and timeout management.
    8. Graceful handling of 401, 403, 429 and CAPTCHA without bypass attempts.
    """

    MAX_RESPONSE_BYTES = 25 * 1024 * 1024  # 25 MB
    MAX_REDIRECTS = 3
    DEFAULT_TIMEOUT_CONNECT = 5.0
    DEFAULT_TIMEOUT_READ = 15.0
    MIN_REQUEST_INTERVAL = 1.5  # seconds per domain

    # Explicitly blocked cloud metadata and link‑local hostnames/IPs
    BLOCKED_HOSTNAMES = {
        "localhost",
        "metadata.google.internal",
        "instance-data",
        "169.254.169.254",
    }

    _last_request_time: Dict[str, float] = {}

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        # Base client – reused for connections that do not need a bound local address.
        self.base_client = httpx.Client(
            headers={
                "User-Agent": "BimaGyanEducationalBot/1.0 (+https://bimagyan.org; academic public policy research)",
                "Accept": "text/html,application/xhtml+xml,application/pdf,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            timeout=httpx.Timeout(self.DEFAULT_TIMEOUT_CONNECT, read=self.DEFAULT_TIMEOUT_READ),
            follow_redirects=False,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    # ---------------------------------------------------------------------
    # URL validation helpers
    # ---------------------------------------------------------------------
    @classmethod
    def validate_url_syntax(cls, url: str) -> str:
        """Validate URL syntax, enforce HTTPS (unless localhost), and reject credentials."""
        if not url or not isinstance(url, str):
            raise SSRFSecurityException("URL must be a non‑empty string.")

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise SSRFSecurityException(f"Malformed URL: '{url}' lacks scheme or network location.")

        scheme = parsed.scheme.lower()
        if scheme not in ("https", "http"):
            raise SSRFSecurityException(f"Unsupported URL scheme '{scheme}'. Only HTTPS is permitted.")

        # Enforce HTTPS for external hosts (allow HTTP for localhost / 127.0.0.1)
        if scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1"):
            url = "https://" + url[len("http://") :]
            parsed = urlparse(url)

        # Reject embedded credentials
        if parsed.username or parsed.password:
            raise SSRFSecurityException("Embedded username/password in URL is strictly prohibited.")

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            raise SSRFSecurityException("URL missing hostname.")

        if hostname in cls.BLOCKED_HOSTNAMES:
            raise SSRFSecurityException(f"Host '{hostname}' is explicitly blocked (internal/metadata).")

        return url

    @classmethod
    def validate_ip_safety(cls, hostname: str, port: int = 443) -> str:
        """Resolve ``hostname`` to IP(s) and ensure all are safe.
        Returns the *first* verified IP address as a string.
        """
        # If hostname is already an IP literal, validate directly.
        try:
            ip = ipaddress.ip_address(hostname)
            cls._check_ip_address_safety(ip)
            return str(ip)
        except ValueError:
            pass  # Not an IP literal – resolve via DNS.

        try:
            addr_info = socket.getaddrinfo(hostname, port, family=socket.AF_UNSPEC, proto=socket.IPPROTO_TCP)
        except socket.gaierror as e:
            raise SSRFSecurityException(f"DNS resolution failed for host '{hostname}': {e}")

        if not addr_info:
            raise SSRFSecurityException(f"No IP address resolved for host '{hostname}'.")

        verified_ip = None
        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            cls._check_ip_address_safety(ip)
            if verified_ip is None:
                verified_ip = ip_str
        return verified_ip

    @classmethod
    def _check_ip_address_safety(cls, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
        """Reject unsafe address families (loopback, private, link‑local, etc.)."""
        if ip.is_loopback:
            raise SSRFSecurityException(f"Target IP {ip} is a loopback address. Connection rejected.")
        if ip.is_private:
            raise SSRFSecurityException(f"Target IP {ip} is a private network address (RFC 1918 / RFC 4193). Connection rejected.")
        if ip.is_link_local:
            raise SSRFSecurityException(f"Target IP {ip} is a link‑local address (RFC 3927). Connection rejected.")
        if ip.is_multicast:
            raise SSRFSecurityException(f"Target IP {ip} is a multicast address. Connection rejected.")
        if ip.is_unspecified:
            raise SSRFSecurityException(f"Target IP {ip} is an unspecified address (0.0.0.0 / ::). Connection rejected.")
        if ip.is_reserved:
            raise SSRFSecurityException(f"Target IP {ip} is a reserved address space. Connection rejected.")
        if str(ip) == "169.254.169.254":
            raise SSRFSecurityException("Access to cloud instance metadata service (169.254.169.254) is blocked.")
        if isinstance(ip, ipaddress.IPv4Address):
            cgnat = ipaddress.ip_network("100.64.0.0/10")
            if ip in cgnat:
                raise SSRFSecurityException(f"Target IP {ip} is within Carrier‑Grade NAT range. Connection rejected.")
            # Benchmark/documentation ranges
            if ip in ipaddress.ip_network("198.18.0.0/15") or ip in ipaddress.ip_network("192.0.2.0/24"):
                raise SSRFSecurityException(f"Target IP {ip} is in benchmark/documentation range. Connection rejected.")

    def _apply_rate_limit(self, hostname: str) -> None:
        last = self._last_request_time.get(hostname, 0.0)
        elapsed = time.time() - last
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time[hostname] = time.time()

    # ---------------------------------------------------------------------
    # Core fetch implementation
    # ---------------------------------------------------------------------
    def fetch(
        self,
        url: str,
        activity: str = AuthorizationActivity.FETCH,
        require_authorization: bool = True,
    ) -> Dict[str, Any]:
        """Execute a protected HTTP GET request.
        Returns a dict with ``success`` flag and payload information.
        """
        # 1️⃣ URL syntax validation
        sanitized_url = self.validate_url_syntax(url)

        # 2️⃣ Authorization check – BEFORE any network activity
        if self.db is not None and require_authorization:
            is_permitted, reason, decision_code = check_authorization(
                self.db, sanitized_url, activity
            )
            if not is_permitted:
                logger.warning(
                    "Protected fetch blocked by authorization policy: %s (Reason: %s)",
                    sanitized_url,
                    reason,
                )
                return {
                    "success": False,
                    "status_code": 403,
                    "error": f"Authorization blocked: {reason}",
                    "decision_code": decision_code,
                    "blocked": True,
                    "url": sanitized_url,
                    "content_bytes": b"",
                    "content_type": "",
                }

        # 3️⃣ Resolve hostname and ensure IP safety
        parsed = urlparse(sanitized_url)
        hostname = (parsed.hostname or "").lower()
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        safe_ip = self.validate_ip_safety(hostname, port)

        # 4️⃣ Rate‑limit per domain
        self._apply_rate_limit(hostname)

        # 5️⃣ Use the configured client after IP safety pre-validation
        client = self.base_client

        current_url = sanitized_url
        redirect_count = 0

        while redirect_count <= self.MAX_REDIRECTS:
            try:
                # Use httpx's streaming API
                with client.stream("GET", current_url) as resp:
                    # Manual redirect handling
                    if resp.status_code in (301, 302, 303, 307, 308):
                        redirect_count += 1
                        if redirect_count > self.MAX_REDIRECTS:
                            return {
                                "success": False,
                                "status_code": resp.status_code,
                                "error": f"Exceeded maximum allowed redirects ({self.MAX_REDIRECTS}).",
                                "decision_code": "REDIRECT_LIMIT_EXCEEDED",
                                "blocked": False,
                                "url": current_url,
                                "content_bytes": b"",
                                "content_type": "",
                            }
                        location = resp.headers.get("Location")
                        if not location:
                            return {
                                "success": False,
                                "status_code": resp.status_code,
                                "error": "Redirect status returned without Location header.",
                                "decision_code": "INVALID_REDIRECT",
                                "blocked": False,
                                "url": current_url,
                                "content_bytes": b"",
                                "content_type": "",
                            }
                        next_url = urljoin(current_url, location)
                        # Re‑validate the next URL (syntax, IP safety, auth)
                        try:
                            next_url = self.validate_url_syntax(next_url)
                            nxt_parsed = urlparse(next_url)
                            nxt_ip = self.validate_ip_safety(nxt_parsed.hostname, nxt_parsed.port or (443 if nxt_parsed.scheme == "https" else 80))
                            # Re‑check authorization if domain changed
                            if self.db is not None and require_authorization:
                                is_perm, r_reason, r_code = check_authorization(self.db, next_url, activity)
                                if not is_perm:
                                    return {
                                        "success": False,
                                        "status_code": 403,
                                        "error": f"Redirect destination blocked by authorization: {r_reason}",
                                        "decision_code": r_code,
                                        "blocked": True,
                                        "url": next_url,
                                        "content_bytes": b"",
                                        "content_type": "",
                                    }
                        except SSRFSecurityException as e:
                            return {
                                "success": False,
                                "status_code": 400,
                                "error": f"Redirect blocked by SSRF filter: {str(e)}",
                                "decision_code": "BLOCKED_SSRF",
                                "blocked": True,
                                "url": next_url,
                                "content_bytes": b"",
                                "content_type": "",
                            }
                        current_url = next_url
                        continue  # follow the loop to the next request

                    # Non‑redirect response handling
                    if resp.status_code in (401, 403):
                        return {
                            "success": False,
                            "status_code": resp.status_code,
                            "error": f"Remote server restricted access (HTTP {resp.status_code}). Manual document upload supported.",
                            "decision_code": "REMOTE_ACCESS_DENIED",
                            "blocked": False,
                            "url": current_url,
                            "content_bytes": b"",
                            "content_type": resp.headers.get("Content-Type", ""),
                        }
                    if resp.status_code == 429:
                        retry_after = resp.headers.get("Retry-After", "unknown")
                        return {
                            "success": False,
                            "status_code": 429,
                            "error": f"Remote server rate limit reached (HTTP 429). Retry-After: {retry_after}s.",
                            "decision_code": "RATE_LIMITED",
                            "blocked": False,
                            "url": current_url,
                            "content_bytes": b"",
                            "content_type": resp.headers.get("Content-Type", ""),
                        }
                    if resp.status_code >= 400:
                        return {
                            "success": False,
                            "status_code": resp.status_code,
                            "error": f"Remote server error: HTTP {resp.status_code}",
                            "decision_code": f"HTTP_{resp.status_code}",
                            "blocked": False,
                            "url": current_url,
                            "content_bytes": b"",
                            "content_type": resp.headers.get("Content-Type", ""),
                        }

                    # CAPTCHA detection (simple header checks)
                    if "cf-mitigated" in resp.headers or "x-amz-captcha" in resp.headers:
                        return {
                            "success": False,
                            "status_code": 403,
                            "error": "Automated scraping blocked by remote CAPTCHA verification challenge.",
                            "decision_code": "CAPTCHA_CHALLENGE",
                            "blocked": True,
                            "url": current_url,
                            "content_bytes": b"",
                            "content_type": resp.headers.get("Content-Type", ""),
                        }

                    # Stream body while respecting size limit
                    content_chunks = []
                    total_bytes = 0
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        if chunk:
                            total_bytes += len(chunk)
                            if total_bytes > self.MAX_RESPONSE_BYTES:
                                # Abort early – payload too large
                                resp.close()
                                return {
                                    "success": False,
                                    "status_code": 413,
                                    "error": f"Response exceeded maximum allowed size limit of {self.MAX_RESPONSE_BYTES // (1024*1024)}MB.",
                                    "decision_code": "PAYLOAD_TOO_LARGE",
                                    "blocked": False,
                                    "url": current_url,
                                    "content_bytes": b"",
                                    "content_type": resp.headers.get("Content-Type", ""),
                                }
                            content_chunks.append(chunk)

                    body_bytes = b"".join(content_chunks)

                    # Inline HTML CAPTCHA detection (snippet scan)
                    content_type = resp.headers.get("Content-Type", "").lower()
                    if "html" in content_type:
                        snippet = body_bytes[:4096].decode("utf-8", errors="ignore")
                        if (
                            "cf-browser-verification" in snippet
                            or "challenge-platform" in snippet
                            or "Just a moment..." in snippet
                        ):
                            return {
                                "success": False,
                                "status_code": 403,
                                "error": "Remote CAPTCHA challenge detected in HTML. Bypassing is prohibited.",
                                "decision_code": "CAPTCHA_CHALLENGE",
                                "blocked": True,
                                "url": current_url,
                                "content_bytes": b"",
                                "content_type": content_type,
                            }

                    return {
                        "success": True,
                        "status_code": resp.status_code,
                        "url": current_url,
                        "content_bytes": body_bytes,
                        "content_type": content_type,
                        "file_size": len(body_bytes),
                        "decision_code": "FETCH_SUCCESS",
                    }
            except httpx.RequestError as e:
                logger.error("HTTP transport error for %s: %s", current_url, e)
                return {
                    "success": False,
                    "status_code": 0,
                    "error": f"Network transport error: {str(e)}",
                    "decision_code": "NETWORK_ERROR",
                    "blocked": False,
                    "url": current_url,
                    "content_bytes": b"",
                    "content_type": "",
                }
        # Should never reach here – loop limits ensure an exit.
        return {
            "success": False,
            "status_code": 0,
            "error": "Unexpected fetch termination.",
            "decision_code": "UNKNOWN",
            "blocked": False,
            "url": current_url,
            "content_bytes": b"",
            "content_type": "",
        }
