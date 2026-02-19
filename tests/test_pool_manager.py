import threading
import time
import psycopg2.pool

import pytest

from src.agents.pool_manager import (
    AgentPoolManager,
    PoolSaturationError,
    AgentConnectionError,
)


class _FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *args, **kwargs):
        pass


class _FakeConn:
    def cursor(self):
        return _FakeCursor()

    def rollback(self):
        pass


class _FakePool:
    def __init__(self, raise_on_get=False):
        self.raise_on_get = raise_on_get
        self.getconn_called = 0
        self.putconn_called = 0

    def getconn(self):
        self.getconn_called += 1
        if self.raise_on_get:
            raise psycopg2.pool.PoolError("pool exhausted")
        return _FakeConn()

    def putconn(self, conn):
        self.putconn_called += 1


def test_acquire_and_release_increments_and_decrements(monkeypatch):
    fake_pool = _FakePool()
    monkeypatch.setattr("src.agents.pool_manager.get_db_pool", lambda: fake_pool)

    manager = AgentPoolManager()
    before = manager._connection_count

    with manager.get_agent_connection("agent_test") as conn:
        assert manager._connection_count == before + 1
        assert fake_pool.getconn_called == 1
        assert fake_pool.putconn_called == 0

    # after context exit the counter should be decremented and putconn called
    assert manager._connection_count == before
    assert fake_pool.putconn_called == 1


def test_circuit_breaker_triggers_on_high_saturation(monkeypatch):
    fake_pool = _FakePool()
    monkeypatch.setattr("src.agents.pool_manager.get_db_pool", lambda: fake_pool)

    manager = AgentPoolManager()
    # Force the internal counter so estimated saturation > SATURATION_THRESHOLD
    manager._connection_count = 12  # 12 + 8 (UI estimate) = 20 -> saturation 1.0

    with pytest.raises(PoolSaturationError):
        with manager.get_agent_connection("agent_overrun"):
            pass


def test_getconn_retries_then_raises_agentconnectionerror(monkeypatch):
    fake_pool = _FakePool(raise_on_get=True)
    monkeypatch.setattr("src.agents.pool_manager.get_db_pool", lambda: fake_pool)

    manager = AgentPoolManager()

    with pytest.raises(AgentConnectionError):
        with manager.get_agent_connection("failing_agent"):
            pass


def test_concurrent_acquisitions_update_counter(monkeypatch):
    fake_pool = _FakePool()
    monkeypatch.setattr("src.agents.pool_manager.get_db_pool", lambda: fake_pool)

    manager = AgentPoolManager()

    def worker():
        with manager.get_agent_connection("worker"):
            time.sleep(0.1)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)

    t1.start()
    t2.start()

    # Let both threads acquire connections
    time.sleep(0.02)
    assert manager._connection_count == 2

    t1.join()
    t2.join()
    assert manager._connection_count == 0
