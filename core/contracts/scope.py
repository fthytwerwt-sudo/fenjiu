"""Scope anchors and execution-policy contracts.

These contracts contain no real business values. They exist only to keep future
scope propagation and external-action defaults explicit.
"""

from dataclasses import dataclass
import re
from uuid import UUID

from core.contracts.errors import ContractValidationError


_SAFE_SLUG = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")

SYNTHETIC_TENANT_ID = UUID("00000000-0000-4000-8000-000000000001")
SYNTHETIC_PROJECT_ID = UUID("00000000-0000-4000-8000-000000000101")
SYNTHETIC_BUSINESS_LINE_ID = UUID("00000000-0000-4000-8000-000000000201")


def _require_uuid(value: object, code: str) -> None:
    if not isinstance(value, UUID) or value.int == 0:
        raise ContractValidationError(code)


def _require_slug(value: object, code: str) -> None:
    if not isinstance(value, str) or _SAFE_SLUG.fullmatch(value) is None:
        raise ContractValidationError(code)


def _require_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _SAFE_IDENTIFIER.fullmatch(value) is None:
        raise ContractValidationError(code)


def _require_internal_only(is_synthetic: object, external_execution_allowed: object) -> None:
    if not isinstance(is_synthetic, bool):
        raise ContractValidationError("synthetic_marker_required")
    if external_execution_allowed is not False:
        raise ContractValidationError("external_execution_forbidden")


@dataclass(frozen=True)
class TenantContract:
    """Root tenant scope anchor; contract instances carry no business payload."""

    id: UUID
    slug: str
    is_synthetic: bool
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "tenant_id_required")
        _require_slug(self.slug, "tenant_slug_required")
        _require_internal_only(self.is_synthetic, self.external_execution_allowed)


@dataclass(frozen=True)
class ProjectContract:
    """Project scope anchor owned by exactly one tenant."""

    id: UUID
    tenant_id: UUID
    slug: str
    is_synthetic: bool
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "project_id_required")
        _require_uuid(self.tenant_id, "tenant_id_required")
        _require_slug(self.slug, "project_slug_required")
        _require_internal_only(self.is_synthetic, self.external_execution_allowed)


@dataclass(frozen=True)
class BusinessLineContract:
    """Business-line scope anchor owned by one tenant/project pair."""

    id: UUID
    tenant_id: UUID
    project_id: UUID
    slug: str
    is_synthetic: bool
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "business_line_id_required")
        _require_uuid(self.tenant_id, "tenant_id_required")
        _require_uuid(self.project_id, "project_id_required")
        _require_slug(self.slug, "business_line_slug_required")
        _require_internal_only(self.is_synthetic, self.external_execution_allowed)


@dataclass(frozen=True)
class ScopeRef:
    """Non-null compound scope reference required by future commands."""

    tenant_id: UUID
    project_id: UUID
    business_line_id: UUID
    correlation_id: str

    def __post_init__(self) -> None:
        _require_uuid(self.tenant_id, "tenant_id_required")
        _require_uuid(self.project_id, "project_id_required")
        _require_uuid(self.business_line_id, "business_line_id_required")
        _require_identifier(self.correlation_id, "correlation_id_required")


@dataclass(frozen=True)
class ExecutionPolicy:
    """Default external-action gates for the current skeleton."""

    external_send: bool = False
    public_publish: bool = False
    real_quote: bool = False
    payment: bool = False
    order_create: bool = False
    refund: bool = False
    inventory_writeback: bool = False
    real_crawl: bool = False
    real_video: bool = False
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        if self.any_sensitive_action_enabled():
            raise ValueError("sensitive action flags must remain disabled")

    def any_sensitive_action_enabled(self) -> bool:
        """Return true if any action that can cross the local boundary is on."""

        return any(
            (
                self.external_send,
                self.public_publish,
                self.real_quote,
                self.payment,
                self.order_create,
                self.refund,
                self.inventory_writeback,
                self.real_crawl,
                self.real_video,
                self.external_execution_allowed,
                self.business_external_ready,
            )
        )


def synthetic_scope() -> ScopeRef:
    """Return a synthetic-only scope for tests and fixtures."""

    return ScopeRef(
        tenant_id=SYNTHETIC_TENANT_ID,
        project_id=SYNTHETIC_PROJECT_ID,
        business_line_id=SYNTHETIC_BUSINESS_LINE_ID,
        correlation_id="synthetic_correlation",
    )


def default_execution_policy() -> ExecutionPolicy:
    """Return the fail-closed external-action policy."""

    return ExecutionPolicy()
