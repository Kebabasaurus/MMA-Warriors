"""Small, dependency-free helpers shared by the long-running test scripts.

The helpers deliberately do not create data, alter random state, or import the
game. They only add execution context to failures so a test can be rerun with
the same suite, subsystem, seed, and data root.
"""

from contextvars import ContextVar
from dataclasses import dataclass, replace
import inspect
import os
from pathlib import Path


_UNSET = object()


@dataclass(frozen=True)
class TestContext:
    suite: str
    subsystem: str = "suite"
    seed: object = None
    data_root: Path = Path("<unknown>")

    def label(self, subsystem=None):
        active_subsystem = subsystem or self.subsystem
        seed = self.seed if self.seed is not None else "not-set"
        return (
            f"suite={self.suite} subsystem={active_subsystem} "
            f"seed={seed} data_root={self.data_root}"
        )


_CURRENT_CONTEXT = ContextVar("mma_warriors_test_context", default=None)


def runtime_data_root():
    """Return the same data-root identity used by the test/runtime process."""
    override = os.environ.get("MMA_WARRIORS_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    try:
        from constants import DATA_DIR
        return Path(DATA_DIR).resolve()
    except Exception:
        return Path(__file__).resolve().parent


def current_context():
    return _CURRENT_CONTEXT.get()


def update_context(*, subsystem=None, seed=_UNSET):
    """Update the current suite context without affecting test behavior."""
    context = current_context()
    if context is None:
        return None
    changes = {}
    if subsystem is not None:
        changes["subsystem"] = subsystem
    if seed is not _UNSET:
        changes["seed"] = seed
    if changes:
        _CURRENT_CONTEXT.set(replace(context, **changes))
    return current_context()


def caller_name():
    """Return the test function that called the local assertion wrapper."""
    # Both smoke_test.assert_true and stability_test.require call this helper,
    # so two frames up is the meaningful test function in either suite.
    frame = inspect.currentframe()
    try:
        caller = frame.f_back.f_back if frame and frame.f_back else None
        return caller.f_code.co_name if caller else "unknown"
    finally:
        del frame


def contextual_message(message, *, subsystem=None):
    context = current_context()
    if context is None:
        return str(message)
    return f"[{context.label(subsystem)}] {message}"


def run_suite(suite, operation):
    """Run one legacy script entrypoint with a useful failure envelope."""
    context = TestContext(suite=suite, data_root=runtime_data_root())
    token = _CURRENT_CONTEXT.set(context)
    try:
        return operation()
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:
        message = str(exc)
        if message.startswith("[suite="):
            raise
        detail = contextual_message(
            f"{type(exc).__name__}: {message}",
            subsystem=context.subsystem,
        )
        if isinstance(exc, AssertionError):
            raise AssertionError(detail) from exc
        raise RuntimeError(detail) from exc
    finally:
        _CURRENT_CONTEXT.reset(token)
