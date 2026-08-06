"""Typed base errors for skeleton-level policy and boundary failures."""


class FenjiuSkeletonError(Exception):
    """Base error for importable skeleton policy failures."""


class BoundaryViolationError(FenjiuSkeletonError):
    """Raised when a package dependency or execution boundary is violated."""
