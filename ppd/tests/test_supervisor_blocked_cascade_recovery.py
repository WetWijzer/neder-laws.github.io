"""Regression coverage for supervisor blocked-cascade recovery.

The daemon supervisor must be able to recover a board that contains only
blocked domain/recovery work by creating deterministic daemon-repair work. The
important safety property is that this path is local and deterministic: it must
not invoke the LLM repair path just because no normal task is currently
available.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class _TaskCandidate:
    task_id: str
    title: str
    status: str = "blocked"
    labels: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()


def _load_daemon_module() -> Any:
    return importlib.import_module("ppd.daemon.ppd_daemon")


def _candidate_tasks() -> list[_TaskCandidate]:
    return [
        _TaskCandidate(
            task_id="checkbox-900",
            title="Extract PP&D permit requirements",
            labels=("domain",),
            blocked_by=("checkbox-901",),
        ),
        _TaskCandidate(
            task_id="checkbox-901",
            title="Recover failed PP&D extraction fixture",
            labels=("recovery",),
            blocked_by=("checkbox-900",),
        ),
        _TaskCandidate(
            task_id="checkbox-902",
            title="Refresh stale PP&D source manifest",
            labels=("domain", "recovery"),
            blocked_by=("checkbox-900", "checkbox-901"),
        ),
    ]


def _is_daemon_repair_task(value: Any) -> bool:
    text = " ".join(
        str(part)
        for part in (
            getattr(value, "task_id", ""),
            getattr(value, "id", ""),
            getattr(value, "title", ""),
            getattr(value, "kind", ""),
            getattr(value, "source", ""),
            getattr(value, "reason", ""),
            getattr(value, "labels", ""),
        )
    ).lower()
    return "daemon" in text and "repair" in text


def _as_iterable(value: Any) -> Iterable[Any]:
    if value is None:
        return ()
    if isinstance(value, dict):
        for key in ("tasks", "repair_tasks", "candidates", "created_tasks"):
            if key in value:
                nested = value[key]
                if isinstance(nested, Iterable) and not isinstance(nested, (str, bytes)):
                    return nested
                return (nested,)
        return value.values()
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return value
    return (value,)


def _call_blocked_cascade_repair(module: Any, tasks: list[_TaskCandidate], llm_repair: Callable[..., Any]) -> Any:
    names = (
        "recover_blocked_cascade",
        "recover_supervisor_blocked_cascade",
        "plan_blocked_cascade_recovery",
        "plan_supervisor_blocked_cascade_recovery",
        "create_blocked_cascade_repair_tasks",
        "create_deterministic_daemon_repair_tasks",
        "ensure_blocked_cascade_recovery",
    )
    for name in names:
        func = getattr(module, name, None)
        if callable(func):
            for kwargs in (
                {"tasks": tasks, "llm_repair": llm_repair},
                {"tasks": tasks, "repair_with_llm": llm_repair},
                {"tasks": tasks, "llm_repair_callback": llm_repair},
                {"board_tasks": tasks, "llm_repair": llm_repair},
                {"board": tasks, "llm_repair": llm_repair},
            ):
                try:
                    return func(**kwargs)
                except TypeError:
                    continue
            try:
                return func(tasks)
            except TypeError:
                continue

    supervisor_cls = getattr(module, "Supervisor", None) or getattr(module, "DaemonSupervisor", None)
    if supervisor_cls is not None:
        try:
            supervisor = supervisor_cls(llm_repair=llm_repair)
        except TypeError:
            supervisor = supervisor_cls()
            for attr in ("llm_repair", "repair_with_llm", "llm_repair_callback"):
                if hasattr(supervisor, attr):
                    setattr(supervisor, attr, llm_repair)
        for name in names:
            method = getattr(supervisor, name, None)
            if callable(method):
                for kwargs in ({"tasks": tasks}, {"board_tasks": tasks}, {"board": tasks}):
                    try:
                        return method(**kwargs)
                    except TypeError:
                        continue
                try:
                    return method(tasks)
                except TypeError:
                    continue

    raise AssertionError(
        "ppd.daemon.ppd_daemon does not expose a blocked-cascade recovery entry point"
    )


def test_blocked_cascade_uses_deterministic_daemon_repair_without_llm() -> None:
    module = _load_daemon_module()
    llm_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def fail_if_llm_repair_is_invoked(*args: Any, **kwargs: Any) -> None:
        llm_calls.append((args, kwargs))
        raise AssertionError("blocked-cascade recovery must not invoke LLM repair")

    result = _call_blocked_cascade_repair(module, _candidate_tasks(), fail_if_llm_repair_is_invoked)
    repair_tasks = tuple(_as_iterable(result))

    assert llm_calls == []
    assert repair_tasks, "blocked cascade should create deterministic repair work"
    assert any(_is_daemon_repair_task(task) for task in repair_tasks), repair_tasks
