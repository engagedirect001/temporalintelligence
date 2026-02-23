import pytest
from buggy_code import Promise, PromiseState


def test_basic_resolve():
    p = Promise(lambda res, rej: res(42))
    assert p.state == PromiseState.FULFILLED
    assert p.value == 42


def test_basic_reject():
    p = Promise(lambda res, rej: rej(ValueError("oops")))
    assert p.state == PromiseState.REJECTED


def test_then_chain():
    p = Promise(lambda res, rej: res(1))
    p2 = p.then(lambda v: v + 1)
    assert p2.value == 2


def test_no_double_resolution():
    """Bug 1: resolving twice should be ignored."""
    resolve_fn = [None]
    
    def executor(res, rej):
        resolve_fn[0] = res
        res(10)
    
    p = Promise(executor)
    assert p.value == 10
    
    # Second resolve should be ignored
    resolve_fn[0](20)
    assert p.value == 10, "Promise should not be re-resolved"
    assert p.state == PromiseState.FULFILLED


def test_catch_recovers():
    """Bug 3: catch handler should resolve (recover), not reject the next promise."""
    p = Promise(lambda res, rej: rej(ValueError("fail")))
    p2 = p.catch(lambda e: "recovered")
    
    assert p2.state == PromiseState.FULFILLED, \
        f"After catch, promise should be FULFILLED, got {p2.state}"
    assert p2.value == "recovered"


def test_catch_then_chain():
    """After catch recovers, subsequent then should work."""
    p = Promise(lambda res, rej: rej(ValueError("fail")))
    result = []
    
    p2 = p.catch(lambda e: "fixed")
    p3 = p2.then(lambda v: result.append(v))
    
    assert "fixed" in result or p3.state == PromiseState.FULFILLED


def test_then_returns_promise():
    """Bug 2: returning a Promise from then() should chain properly."""
    inner_resolve = [None]
    
    def executor(res, rej):
        inner_resolve[0] = res
    
    p = Promise.resolve(1)
    inner = Promise(executor)
    p2 = p.then(lambda v: inner)
    
    # p2 should be pending until inner resolves
    assert p2.state == PromiseState.PENDING or p2.value is None
    
    # Now resolve inner
    inner_resolve[0](42)
    assert p2.state == PromiseState.FULFILLED
    assert p2.value == 42


def test_promise_all():
    p1 = Promise.resolve(1)
    p2 = Promise.resolve(2)
    p3 = Promise.resolve(3)
    
    result = Promise.all([p1, p2, p3])
    assert result.state == PromiseState.FULFILLED
    assert result.value == [1, 2, 3]


def test_finally_called():
    called = [False]
    p = Promise.resolve(42)
    p.finally_(lambda: called.__setitem__(0, True))
    assert called[0] is True


def test_rejection_propagates():
    p = Promise(lambda res, rej: rej(ValueError("err")))
    p2 = p.then(lambda v: v + 1)
    assert p2.state == PromiseState.REJECTED
