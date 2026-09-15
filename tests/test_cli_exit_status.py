from __future__ import annotations

from types import SimpleNamespace

import museum_pipeline.cli as cli
import museum_pipeline.harness.runner as runner_mod
import museum_pipeline.harness.runtime as runtime_mod


class FakeConn:
    def close(self):
        pass


class FakeStore:
    def __init__(self):
        self.conn = FakeConn()

    def connect(self):
        return self.conn

    def pick_objects(self, conn, limit, ids=None, collections=None):
        return [{"obj_id": value} for value in (ids or [])]


class FakeState:
    def __init__(self, failed_ids):
        self.failed_ids = set(failed_ids)

    def failed(self, conn, obj_id):
        return obj_id in self.failed_ids


def make_args():
    return SimpleNamespace(
        workflow="core",
        ids="TEST-001",
        ids_file=None,
        collection=None,
        force=False,
        retry_failed=False,
        count=20,
        workers=1,
    )


def make_cfg():
    return SimpleNamespace(
        workflow=SimpleNamespace(
            data={"name": "core"},
            modules={},
        ),
        hardware=SimpleNamespace(
            default_workers=1,
        ),
    )


def install_fakes(monkeypatch, failed_ids):
    cfg = make_cfg()

    class FakeRuntime:
        def __init__(self, config):
            self.cfg = config
            self.store = FakeStore()
            self.state = FakeState(failed_ids)

    class FakeRunner:
        def __init__(self, runtime, workers):
            self.runtime = runtime
            self.workers = workers

        def run(self, objects, force=False, retry_failed=False):
            return None

    monkeypatch.setattr(
        cli,
        "_load",
        lambda workflow=None: (None, cfg),
    )
    monkeypatch.setattr(
        runtime_mod,
        "Runtime",
        FakeRuntime,
    )
    monkeypatch.setattr(
        runner_mod,
        "WorkflowRunner",
        FakeRunner,
    )


def test_cmd_run_returns_nonzero_when_selected_object_failed(monkeypatch):
    install_fakes(monkeypatch, {"TEST-001"})

    assert cli.cmd_run(make_args()) == 1


def test_cmd_run_returns_zero_when_selected_object_succeeded(monkeypatch):
    install_fakes(monkeypatch, set())

    assert cli.cmd_run(make_args()) == 0
