"""Deterministic validation for PP&D public source discovery records.

The validator is intentionally side-effect free. It does not fetch URLs, consult
robots.txt, or inspect authenticated surfaces. It only classifies discovery
records that were already observed by a public-source parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse


ALLOWED_PUBLIC_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

SUPPORTED_SCHEMES = frozenset({"http", "https"})

PRIVATE_PATH_MARKERS = (
    "/account",
    "/admin",
    "/auth",
    "/dashboard",
    "/login",
    "/logout",
    "/myaccount",
    "/my-permits",
    "/mypermits",
    "/oauth",
    "/profile",
    "/register",
    "/saml",
    "/secure",
    "/signin",
    "/sign-in",
    "/user",
)

PRIVATE_QUERY_MARKERS = (
    "access_token=",
    "auth=",
    "code=",
    "id_token=",
    "session=",
    "ticket=",
    "token=",
)

PPD_GUIDANCE_HOST = "www.portland.gov"
PPD_GUIDANCE_PREFIX = "/ppd"
PORTLAND_MAPS_HOST = "www.portlandmaps.com"


@dataclass(frozen=True)
class DiscoveryValidationFinding:
    """A deterministic validation result for one discovered URL."""

    record_id: str
    url: str
    decision: str
    reason_code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "record_id": self.record_id,
            "url": self.url,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "message": self.message,
        }


def validate_discovery_records(
    records: Iterable[Mapping[str, Any]],
) -> list[DiscoveryValidationFinding]:
    """Validate discovery records without network access.

    Expected record fields are deliberately small so fixtures can be authored by
    hand: ``record_id``, ``url``, ``source_url``, and optional ``link_text``.
    Additional fields are ignored.
    """

    findings: list[DiscoveryValidationFinding] = []
    for index, record in enumerate(records):
        findings.append(validate_discovery_record(record, fallback_id=str(index)))
    return findings


def validate_discovery_record(
    record: Mapping[str, Any], fallback_id: str = "0"
) -> DiscoveryValidationFinding:
    record_id = str(record.get("record_id") or record.get("id") or fallback_id)
    url = str(record.get("url") or "")
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    query = parsed.query.lower()

    if not scheme or not host:
        return DiscoveryValidationFinding(
            record_id=record_id,
            url=url,
            decision="skip",
            reason_code="invalid_url",
            message="Discovered URL is not absolute.",
        )

    if scheme not in SUPPORTED_SCHEMES:
        return DiscoveryValidationFinding(
            record_id=record_id,
            url=url,
            decision="skip",
            reason_code="unsupported_scheme",
            message="Discovery URL uses a scheme outside deterministic public crawl support.",
        )

    if host not in ALLOWED_PUBLIC_HOSTS:
        return DiscoveryValidationFinding(
            record_id=record_id,
            url=url,
            decision="skip",
            reason_code="outside_allowlist",
            message="Discovery URL host is outside the PP&D public source allowlist.",
        )

    if _looks_private_or_authenticated(path, query):
        return DiscoveryValidationFinding(
            record_id=record_id,
            url=url,
            decision="skip",
            reason_code="private_authenticated",
            message="Discovery URL appears to require private, account, or authenticated access.",
        )

    if host == PORTLAND_MAPS_HOST and not _is_public_portland_maps_reference(record):
        return DiscoveryValidationFinding(
            record_id=record_id,
            url=url,
            decision="skip",
            reason_code="portland_maps_not_from_ppd_guidance",
            message="Portland Maps URLs are allowed only when linked from public PP&D guidance.",
        )

    return DiscoveryValidationFinding(
        record_id=record_id,
        url=url,
        decision="allow",
        reason_code="allowed_public_source",
        message="Discovery URL is within the deterministic PP&D public source policy.",
    )


def _looks_private_or_authenticated(path: str, query: str) -> bool:
    if any(marker in path for marker in PRIVATE_PATH_MARKERS):
        return True
    if any(marker in query for marker in PRIVATE_QUERY_MARKERS):
        return True
    return False


def _is_public_portland_maps_reference(record: Mapping[str, Any]) -> bool:
    source_url = str(record.get("source_url") or record.get("source_page_url") or "")
    parsed_source = urlparse(source_url)
    source_host = parsed_source.netloc.lower()
    source_path = parsed_source.path.lower()
    if source_host == PPD_GUIDANCE_HOST and source_path.startswith(PPD_GUIDANCE_PREFIX):
        return True

    relationship = str(record.get("relationship") or record.get("link_role") or "").lower()
    return relationship == "ppd_public_portland_maps_reference"
