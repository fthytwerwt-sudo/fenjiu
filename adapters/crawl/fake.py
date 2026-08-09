"""P05-01 zero-network synthetic crawl adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from core.contracts import DataState, ScopeRef, synthetic_scope
from modules.leads import (
    CrawlBoundaryError,
    EvidenceLocator,
    PublicFieldCandidate,
    PublicSnapshot,
    SourcePolicy,
    validate_policy_for_url,
)
from modules.leads.source_policy import (
    digest_identifier,
    field_payload_hash,
    require_page_payload,
    require_synthetic_url,
    reject_contact_field_name,
    selector_hash,
    source_url_hash,
    validate_allowed_public_fields,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _policy_scope(policy: SourcePolicy | None) -> ScopeRef:
    if isinstance(policy, SourcePolicy):
        return policy.scope
    return synthetic_scope()


def _policy_version(policy: SourcePolicy | None) -> str:
    if isinstance(policy, SourcePolicy) and policy.policy_id is not None:
        return policy.policy_id
    return "source_policy_missing"


def _field_value(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise CrawlBoundaryError(f"{key}_required")
    return value


class FakeCrawlPort:
    """Fake CrawlPort that hashes synthetic fixture pages without network IO."""

    def __init__(
        self,
        *,
        pages: Mapping[str, Mapping[str, object]],
        audit_log: object,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._pages = dict(pages)
        self._audit_log = audit_log
        self._now = now or _now_utc
        self._snapshots: dict[str, tuple[PublicSnapshot, Mapping[str, object]]] = {}
        self._external_fetch_count = 0

    @property
    def external_fetch_count(self) -> int:
        return self._external_fetch_count

    def fetch_snapshot(self, url: str, policy: SourcePolicy | None) -> PublicSnapshot:
        try:
            allowed_policy = validate_policy_for_url(policy, url)
            page = require_page_payload(self._pages.get(require_synthetic_url(url)))
        except CrawlBoundaryError as exc:
            self._record(
                event_kind="crawl_policy_denied",
                result_code=exc.code,
                policy=policy,
                url=url,
            )
            raise

        html = _field_value(page, "html")
        content_hash = sha256(html.encode("utf-8")).hexdigest()
        url_hash = source_url_hash(url)
        snapshot_ref = "snapshot:" + digest_identifier(
            allowed_policy.scope.tenant_id,
            allowed_policy.scope.project_id,
            allowed_policy.scope.business_line_id,
            allowed_policy.policy_id,
            url_hash,
            content_hash,
        )[:32]
        snapshot = PublicSnapshot(
            scope=allowed_policy.scope,
            policy_id=allowed_policy.policy_id,
            snapshot_ref=snapshot_ref,
            content_hash=content_hash,
            source_url_hash=url_hash,
            retrieved_at=self._now(),
            http_policy_result="synthetic_zero_network",
            data_state=DataState.FIXTURE,
            is_synthetic=True,
            external_execution_allowed=False,
            business_external_ready=False,
        )
        self._snapshots[snapshot.snapshot_ref] = (snapshot, page)
        self._record(
            event_kind="crawl_snapshot_created",
            result_code="snapshot_created",
            policy=allowed_policy,
            url=url,
            extra_metadata={
                "snapshot_ref": snapshot.snapshot_ref,
                "field_count": len(page.get("fields", ())),
            },
        )
        return snapshot

    def extract_public_fields(
        self,
        snapshot_ref: str,
        policy: SourcePolicy,
    ) -> tuple[PublicFieldCandidate, ...]:
        try:
            validate_allowed_public_fields(policy.allowed_fields)
        except CrawlBoundaryError as exc:
            self._record(
                event_kind="crawl_field_denied",
                result_code=exc.code,
                policy=policy,
                url_hash=self._snapshot_url_hash(snapshot_ref),
            )
            raise
        snapshot, page = self._snapshot_for_policy(snapshot_ref, policy)
        fields = page.get("fields")
        if not isinstance(fields, list):
            raise CrawlBoundaryError("synthetic_fields_required")

        candidates: list[PublicFieldCandidate] = []
        for field in fields:
            if not isinstance(field, Mapping):
                raise CrawlBoundaryError("synthetic_field_required")
            field_name = _field_value(field, "field_name")
            try:
                reject_contact_field_name(field_name)
            except CrawlBoundaryError as exc:
                self._record(
                    event_kind="crawl_field_denied",
                    result_code=exc.code,
                    policy=policy,
                    url_hash=snapshot.source_url_hash,
                    extra_metadata={
                        "snapshot_ref": snapshot.snapshot_ref,
                        "blocked_public_field_hash": sha256(field_name.encode("utf-8")).hexdigest(),
                    },
                )
                raise
            if field_name not in policy.allowed_fields:
                continue
            evidence = EvidenceLocator(
                scope=policy.scope,
                snapshot_ref=snapshot.snapshot_ref,
                field_name=field_name,
                selector_hash=selector_hash(field.get("selector")),
                source_url_hash=snapshot.source_url_hash,
            )
            candidates.append(
                PublicFieldCandidate(
                    scope=policy.scope,
                    snapshot_ref=snapshot.snapshot_ref,
                    field_name=field_name,
                    value_hash=field_payload_hash(field.get("value")),
                    evidence=evidence,
                    data_state=DataState.FIXTURE,
                    is_synthetic=True,
                    external_execution_allowed=False,
                    business_external_ready=False,
                )
            )

        self._record(
            event_kind="crawl_fields_extracted",
            result_code="fields_extracted",
            policy=policy,
            url_hash=snapshot.source_url_hash,
            extra_metadata={
                "snapshot_ref": snapshot.snapshot_ref,
                "field_count": len(candidates),
            },
        )
        return tuple(candidates)

    def export_external_snapshot(self, snapshot_ref: str, policy: SourcePolicy) -> None:
        snapshot, _ = self._snapshot_for_policy(snapshot_ref, policy)
        self._record(
            event_kind="crawl_export_denied",
            result_code="external_export_forbidden",
            policy=policy,
            url_hash=snapshot.source_url_hash,
            extra_metadata={"snapshot_ref": snapshot.snapshot_ref},
        )
        raise CrawlBoundaryError("external_export_forbidden")

    def _snapshot_for_policy(
        self,
        snapshot_ref: str,
        policy: SourcePolicy,
    ) -> tuple[PublicSnapshot, Mapping[str, object]]:
        item = self._snapshots.get(snapshot_ref)
        if item is None:
            self._record(
                event_kind="crawl_policy_denied",
                result_code="snapshot_ref_unknown",
                policy=policy,
                url_hash="0" * 64,
            )
            raise CrawlBoundaryError("snapshot_ref_unknown")
        snapshot, page = item
        validate_policy_for_url(policy, self._url_for_snapshot_ref(snapshot_ref))
        if snapshot.scope != policy.scope:
            self._record(
                event_kind="crawl_policy_denied",
                result_code="cross_scope_forbidden",
                policy=policy,
                url_hash=snapshot.source_url_hash,
                extra_metadata={"snapshot_ref": snapshot.snapshot_ref},
            )
            raise CrawlBoundaryError("cross_scope_forbidden")
        return snapshot, page

    def _url_for_snapshot_ref(self, snapshot_ref: str) -> str:
        item = self._snapshots.get(snapshot_ref)
        if item is None:
            return "https://missing.invalid/source"
        snapshot, _ = item
        for url in self._pages:
            if source_url_hash(url) == snapshot.source_url_hash:
                return url
        return "https://missing.invalid/source"

    def _snapshot_url_hash(self, snapshot_ref: str) -> str:
        item = self._snapshots.get(snapshot_ref)
        if item is None:
            return "0" * 64
        snapshot, _ = item
        return snapshot.source_url_hash

    def _record(
        self,
        *,
        event_kind: str,
        result_code: str,
        policy: SourcePolicy | None,
        url: str | None = None,
        url_hash: str | None = None,
        extra_metadata: Mapping[str, object] | None = None,
    ) -> None:
        record = getattr(self._audit_log, "record", None)
        if not callable(record):
            raise CrawlBoundaryError("audit_persistence_required")
        safe_url_hash = url_hash if url_hash is not None else source_url_hash(url)
        metadata: dict[str, Any] = {
            "source_url_hash": safe_url_hash,
            "external_fetch_count": self._external_fetch_count,
            "reason_code": result_code,
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        record(
            event_kind=event_kind,
            actor_ref="crawl_policy_guard",
            scope=_policy_scope(policy),
            command_ref="crawl.fetch_snapshot",
            target_ref="source:" + safe_url_hash[:32],
            policy_version=_policy_version(policy),
            subject_version=1,
            result_code=result_code,
            metadata=metadata,
        )


__all__ = ["FakeCrawlPort"]
