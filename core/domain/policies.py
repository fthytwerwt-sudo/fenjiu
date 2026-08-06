"""Domain-level policy placeholders with fail-closed defaults."""

from core.contracts.scope import ExecutionPolicy


def external_actions_disabled(policy: ExecutionPolicy) -> bool:
    """Return true only when every external-action flag is disabled."""

    return not any(policy.__dict__.values())
