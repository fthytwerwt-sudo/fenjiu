"""P05-01 synthetic public-source policy and evidence contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import re
from typing import Mapping

from core.contracts import ContractValidationError, DataState, ScopeRef


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SYNTHETIC_HTTPS_URL = re.compile(
    r"^https://[a-z0-9.-]+\.invalid(?:/[A-Za-z0-9._~!$&'()*+,;=:@/-]*)?$"
)
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)
_CONTACT_FIELD_SEMANTICS = re.compile(
    r"(?i)(contact|e[-_]?mail|phone|whatsapp|wechat|telegram|linkedin|outreach)"
)


class CrawlBoundaryError(ContractValidationError):
    """Stable, value-free P05-01 crawl/policy boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _boundary(code: str) -> CrawlBoundaryError:
    return CrawlBoundaryError(code)


def _reject_sensitive_text(value: object) -> None:
    if isinstance(value, str) and _SENSITIVE.search(value) is not None:
        raise _boundary("sensitive_metadata_forbidden")


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _require_optional_identifier(value: object, code: str) -> str | None:
    if value is None:
        return None
    return _require_identifier(value, code)


def _require_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise _boundary("scope_required")
    _require_identifier(value.correlation_id, "correlation_id_required")
    return value


def _require_hash(value: object, code: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise _boundary(code)
    return value


def _require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


def _require_bool(value: object, code: str) -> bool:
    if not isinstance(value, bool):
        raise _boundary(code)
    return value


def _require_positive_int(value: object, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise _boundary(code)
    return value


def _require_synthetic_fixture_boundary(
    *,
    data_state: object,
    is_synthetic: object,
    external_execution_allowed: object,
    business_external_ready: object,
) -> None:
    if data_state is not DataState.FIXTURE:
        raise _boundary("fixture_data_state_required")
    if is_synthetic is not True:
        raise _boundary("synthetic_input_required")
    if external_execution_allowed is not False:
        raise _boundary("external_execution_forbidden")
    if business_external_ready is not False:
        raise _boundary("business_external_ready_forbidden")


def require_synthetic_url(value: object, code: str = "synthetic_url_required") -> str:
    if not isinstance(value, str) or _SYNTHETIC_HTTPS_URL.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def source_url_hash(url: object) -> str:
    return sha256(require_synthetic_url(url).encode("utf-8")).hexdigest()


def digest_identifier(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _validate_identifier_tuple(value: object, code: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise _boundary(code)
    return tuple(_require_identifier(item, code) for item in value)


def reject_contact_field_name(value: object) -> str:
    field_name = _require_identifier(value, "field_name_required")
    if _CONTACT_FIELD_SEMANTICS.search(field_name) is not None:
        raise _boundary("public_field_forbidden")
    return field_name


def validate_allowed_public_fields(value: object) -> tuple[str, ...]:
    allowed_fields = _validate_identifier_tuple(value, "allowed_fields_required")
    return tuple(reject_contact_field_name(field_name) for field_name in allowed_fields)


def _validate_prefix_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise _boundary("source_allowlist_required")
    return tuple(require_synthetic_url(item, "source_allowlist_required") for item in value)


@dataclass(frozen=True)
class SourcePolicy:
    """Synthetic source policy draft evaluated before any fake snapshot."""

    policy_id: str | None
    scope: ScopeRef
    purpose: str
    owner_ref: str | None
    allowed_url_prefixes: tuple[str, ...]
    robots_review_ref: str | None
    robots_allowed: bool | None
    terms_review_ref: str | None
    terms_allowed: bool | None
    allowed_fields: tuple[str, ...]
    max_frequency_per_day: int
    retention_days: int
    manual_review_required: bool
    stop_conditions: tuple[str, ...]
    data_state: DataState
    is_synthetic: bool
    external_execution_allowed: bool
    business_external_ready: bool
    login_required: bool = False
    captcha_required: bool = False
    private_source: bool = False
    authentication_required: bool = False

    def __post_init__(self) -> None:
        _require_optional_identifier(self.policy_id, "source_policy_required")
        _require_scope(self.scope)
        _require_identifier(self.purpose, "source_purpose_required")
        _require_optional_identifier(self.owner_ref, "source_owner_required")
        object.__setattr__(self, "allowed_url_prefixes", _validate_prefix_tuple(self.allowed_url_prefixes))
        _require_optional_identifier(self.robots_review_ref, "robots_review_required")
        if self.robots_allowed is not None:
            _require_bool(self.robots_allowed, "robots_status_required")
        _require_optional_identifier(self.terms_review_ref, "terms_review_required")
        if self.terms_allowed is not None:
            _require_bool(self.terms_allowed, "terms_status_required")
        object.__setattr__(self, "allowed_fields", validate_allowed_public_fields(self.allowed_fields))
        _require_positive_int(self.max_frequency_per_day, "source_frequency_required")
        _require_positive_int(self.retention_days, "retention_policy_required")
        _require_bool(self.manual_review_required, "manual_review_required")
        object.__setattr__(self, "stop_conditions", _validate_identifier_tuple(self.stop_conditions, "stop_conditions_required"))
        for value, code in (
            (self.login_required, "login_required_status_required"),
            (self.captcha_required, "captcha_status_required"),
            (self.private_source, "private_source_status_required"),
            (self.authentication_required, "authentication_status_required"),
        ):
            _require_bool(value, code)
        _require_synthetic_fixture_boundary(
            data_state=self.data_state,
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            business_external_ready=self.business_external_ready,
        )


@dataclass(frozen=True)
class PublicSnapshot:
    scope: ScopeRef
    policy_id: str
    snapshot_ref: str
    content_hash: str
    source_url_hash: str
    retrieved_at: datetime
    http_policy_result: str
    data_state: DataState
    is_synthetic: bool
    external_execution_allowed: bool
    business_external_ready: bool

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.policy_id, "source_policy_required")
        _require_identifier(self.snapshot_ref, "snapshot_ref_required")
        _require_hash(self.content_hash, "content_hash_required")
        _require_hash(self.source_url_hash, "source_url_hash_required")
        _require_time(self.retrieved_at, "retrieved_at_required")
        _require_identifier(self.http_policy_result, "http_policy_result_required")
        _require_synthetic_fixture_boundary(
            data_state=self.data_state,
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            business_external_ready=self.business_external_ready,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "scope": {
                "tenant_id": str(self.scope.tenant_id),
                "project_id": str(self.scope.project_id),
                "business_line_id": str(self.scope.business_line_id),
            },
            "policy_id": self.policy_id,
            "snapshot_ref": self.snapshot_ref,
            "content_hash": self.content_hash,
            "source_url_hash": self.source_url_hash,
            "retrieved_at": self.retrieved_at.isoformat(),
            "http_policy_result": self.http_policy_result,
            "data_state": self.data_state.value,
            "is_synthetic": self.is_synthetic,
            "external_execution_allowed": self.external_execution_allowed,
            "business_external_ready": self.business_external_ready,
        }


@dataclass(frozen=True)
class EvidenceLocator:
    scope: ScopeRef
    snapshot_ref: str
    field_name: str
    selector_hash: str
    source_url_hash: str

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.snapshot_ref, "snapshot_ref_required")
        reject_contact_field_name(self.field_name)
        _require_hash(self.selector_hash, "selector_hash_required")
        _require_hash(self.source_url_hash, "source_url_hash_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "snapshot_ref": self.snapshot_ref,
            "field_name": self.field_name,
            "selector_hash": self.selector_hash,
            "source_url_hash": self.source_url_hash,
        }


@dataclass(frozen=True)
class PublicFieldCandidate:
    scope: ScopeRef
    snapshot_ref: str
    field_name: str
    value_hash: str
    evidence: EvidenceLocator
    data_state: DataState
    is_synthetic: bool
    external_execution_allowed: bool
    business_external_ready: bool

    def __post_init__(self) -> None:
        scope = _require_scope(self.scope)
        _require_identifier(self.snapshot_ref, "snapshot_ref_required")
        reject_contact_field_name(self.field_name)
        _require_hash(self.value_hash, "value_hash_required")
        if not isinstance(self.evidence, EvidenceLocator):
            raise _boundary("evidence_locator_required")
        if self.evidence.scope != scope or self.evidence.snapshot_ref != self.snapshot_ref:
            raise _boundary("evidence_scope_mismatch")
        _require_synthetic_fixture_boundary(
            data_state=self.data_state,
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            business_external_ready=self.business_external_ready,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "snapshot_ref": self.snapshot_ref,
            "field_name": self.field_name,
            "value_hash": self.value_hash,
            "evidence": self.evidence.safe_summary(),
            "data_state": self.data_state.value,
            "is_synthetic": self.is_synthetic,
            "external_execution_allowed": self.external_execution_allowed,
            "business_external_ready": self.business_external_ready,
        }


def validate_policy_for_url(policy: SourcePolicy | None, url: str) -> SourcePolicy:
    if policy is None or policy.policy_id is None:
        raise _boundary("source_policy_required")
    if policy.owner_ref is None:
        raise _boundary("source_owner_required")
    if policy.robots_review_ref is None:
        raise _boundary("robots_review_required")
    if policy.robots_allowed is not True:
        raise _boundary("robots_denied")
    if policy.terms_review_ref is None:
        raise _boundary("terms_review_required")
    if policy.terms_allowed is not True:
        raise _boundary("terms_denied")
    validate_allowed_public_fields(policy.allowed_fields)
    if policy.login_required is True:
        raise _boundary("login_required_source_forbidden")
    if policy.captcha_required is True:
        raise _boundary("captcha_source_forbidden")
    if policy.private_source is True:
        raise _boundary("private_source_forbidden")
    if policy.authentication_required is True:
        raise _boundary("authentication_source_forbidden")
    safe_url = require_synthetic_url(url)
    if not any(safe_url.startswith(prefix) for prefix in policy.allowed_url_prefixes):
        raise _boundary("source_url_not_allowed")
    return policy


def field_payload_hash(value: object) -> str:
    if not isinstance(value, str):
        raise _boundary("field_value_required")
    _reject_sensitive_text(value)
    return sha256(value.encode("utf-8")).hexdigest()


def selector_hash(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise _boundary("selector_required")
    _reject_sensitive_text(value)
    return sha256(value.encode("utf-8")).hexdigest()


def require_page_payload(page: object) -> Mapping[str, object]:
    if not isinstance(page, Mapping):
        raise _boundary("synthetic_page_required")
    html = page.get("html")
    fields = page.get("fields")
    if not isinstance(html, str) or not html:
        raise _boundary("synthetic_page_required")
    if not isinstance(fields, list):
        raise _boundary("synthetic_fields_required")
    _reject_sensitive_text(html)
    return page


__all__ = [
    "CrawlBoundaryError",
    "EvidenceLocator",
    "PublicFieldCandidate",
    "PublicSnapshot",
    "SourcePolicy",
    "digest_identifier",
    "field_payload_hash",
    "require_page_payload",
    "require_synthetic_url",
    "reject_contact_field_name",
    "selector_hash",
    "source_url_hash",
    "validate_allowed_public_fields",
    "validate_policy_for_url",
]
