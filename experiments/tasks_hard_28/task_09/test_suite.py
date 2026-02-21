import pytest
import asyncio
from buggy_code import AsyncTaskScheduler


@pytest.fixture
def scheduler():
    return AsyncTaskScheduler()


def test_simple_dependency(scheduler):
    async def task_a(deps):
        return "a_result"
    async def task_b(deps):
        return deps["a"] + "_b"
    
    scheduler.add_task("a", task_a)
    scheduler.add_task("b", task_b, dependencies=["a"])
    
    results = asyncio.get_event_loop().run_until_complete(scheduler.run_all(timeout=5))
    assert results["a"] == "a_result"
    assert results["b"] == "a_result_b"


def test_execution_order(scheduler):
    async def make_task(name):
        async def task(deps):
            await asyncio.sleep(0.01)
            return name
        return task
    
    async def run():
        scheduler.add_task("a", await make_task("a"))
        scheduler.add_task("b", await make_task("b"), dependencies=["a"])
        scheduler.add_task("c", await make_task("c"), dependencies=["a"])
        scheduler.add_task("d", await make_task("d"), dependencies=["b", "c"])
        await scheduler.run_all(timeout=5)
        
        assert scheduler.execution_order.index("a") < scheduler.execution_order.index("b")
        assert scheduler.execution_order.index("a") < scheduler.execution_order.index("c")
        assert scheduler.execution_order.index("b") < scheduler.execution_order.index("d")
        assert scheduler.execution_order.index("c") < scheduler.execution_order.index("d")
    
    asyncio.get_event_loop().run_until_complete(run())


def test_cycle_detection(scheduler):
    """Bug in has_cycle: reports false positives for diamond dependencies."""
    async def noop(deps):
        return None
    
    # Diamond: a -> b, a -> c, b -> d, c -> d  (NO cycle)
    scheduler.add_task("a", noop)
    scheduler.add_task("b", noop, dependencies=["a"])
    scheduler.add_task("c", noop, dependencies=["a"])
    scheduler.add_task("d", noop, dependencies=["b", "c"])
    
    assert scheduler.has_cycle() is False, "Diamond dependency is not a cycle"


def test_actual_cycle_detected(scheduler):
    async def noop(deps):
        return None
    
    scheduler.add_task("a", noop, dependencies=["c"])
    scheduler.add_task("b", noop, dependencies=["a"])
    scheduler.add_task("c", noop, dependencies=["b"])
    
    assert scheduler.has_cycle() is True


def test_task_failure_propagation(scheduler):
    """Bug 1: failed task should not leave dependents hanging."""
    async def failing_task(deps):
        raise ValueError("task failed")
    
    async def dependent_task(deps):
        return "should_not_run"
    
    scheduler.add_task("a", failing_task)
    scheduler.add_task("b", dependent_task, dependencies=["a"])
    
    with pytest.raises((ValueError, asyncio.TimeoutError)):
        asyncio.get_event_loop().run_until_complete(scheduler.run_all(timeout=2))
    
    # b should not have completed
    assert "b" not in scheduler.results


def test_independent_parallel(scheduler):
    """Independent tasks should run in parallel."""
    async def slow_task(deps):
        await asyncio.sleep(0.1)
        return "done"
    
    scheduler.add_task("a", slow_task)
    scheduler.add_task("b", slow_task)
    scheduler.add_task("c", slow_task)
    
    import time
    start = time.monotonic()
    asyncio.get_event_loop().run_until_complete(scheduler.run_all(timeout=5))
    elapsed = time.monotonic() - start
    
    assert elapsed < 0.5, "Independent tasks should run in parallel"
    assert len(scheduler.results) == 3
