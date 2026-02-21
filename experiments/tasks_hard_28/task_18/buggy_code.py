"""
Task 18: Promise/Future Chain with Error Handling State Machine
Category: Combined — state machine + async pattern bugs
"""
from enum import Enum, auto
from typing import Callable, Any, Optional


class PromiseState(Enum):
    PENDING = auto()
    FULFILLED = auto()
    REJECTED = auto()


class Promise:
    """A simple Promise implementation with chaining."""
    
    def __init__(self, executor=None):
        self.state = PromiseState.PENDING
        self.value = None
        self.error = None
        self._then_handlers = []
        self._catch_handlers = []
        self._finally_handlers = []
        
        if executor:
            try:
                executor(self._resolve, self._reject)
            except Exception as e:
                self._reject(e)
    
    def _resolve(self, value):
        # Bug 1: doesn't check if already settled — allows double resolution
        self.state = PromiseState.FULFILLED
        self.value = value
        self._run_handlers()
    
    def _reject(self, error):
        # Same bug 1: no guard against already settled
        self.state = PromiseState.REJECTED
        self.error = error
        self._run_handlers()
    
    def _run_handlers(self):
        if self.state == PromiseState.FULFILLED:
            for handler, next_promise in self._then_handlers:
                try:
                    result = handler(self.value)
                    if isinstance(result, Promise):
                        # Bug 2: doesn't chain the inner promise correctly
                        # Should wait for inner promise, then resolve next_promise
                        result._then_handlers.append(
                            (lambda v: next_promise._resolve(v), None)
                        )
                    else:
                        next_promise._resolve(result)
                except Exception as e:
                    next_promise._reject(e)
        
        elif self.state == PromiseState.REJECTED:
            if self._catch_handlers:
                for handler, next_promise in self._catch_handlers:
                    try:
                        result = handler(self.error)
                        # Bug 3: after catching, should resolve (not reject) the next promise
                        next_promise._reject(result)
                    except Exception as e:
                        next_promise._reject(e)
            else:
                # Propagate rejection to then-handlers' promises
                for _, next_promise in self._then_handlers:
                    next_promise._reject(self.error)
        
        for handler in self._finally_handlers:
            try:
                handler()
            except Exception:
                pass
    
    def then(self, on_fulfilled):
        next_promise = Promise()
        if self.state == PromiseState.FULFILLED:
            try:
                result = on_fulfilled(self.value)
                next_promise._resolve(result)
            except Exception as e:
                next_promise._reject(e)
        elif self.state == PromiseState.REJECTED:
            next_promise._reject(self.error)
        else:
            self._then_handlers.append((on_fulfilled, next_promise))
        return next_promise
    
    def catch(self, on_rejected):
        next_promise = Promise()
        if self.state == PromiseState.REJECTED:
            try:
                result = on_rejected(self.error)
                next_promise._resolve(result)
            except Exception as e:
                next_promise._reject(e)
        elif self.state == PromiseState.FULFILLED:
            next_promise._resolve(self.value)
        else:
            self._catch_handlers.append((on_rejected, next_promise))
        return next_promise
    
    def finally_(self, handler):
        self._finally_handlers.append(handler)
        return self
    
    @staticmethod
    def resolve(value):
        return Promise(lambda res, rej: res(value))
    
    @staticmethod
    def reject(error):
        return Promise(lambda res, rej: rej(error))
    
    @staticmethod
    def all(promises):
        """Wait for all promises to resolve."""
        results = [None] * len(promises)
        count = [0]
        
        def make_resolver(result_promise):
            def on_resolve(idx):
                def handler(value):
                    results[idx] = value
                    count[0] += 1
                    if count[0] == len(promises):
                        result_promise._resolve(results)
                return handler
            return on_resolve
        
        result_promise = Promise()
        resolver = make_resolver(result_promise)
        
        for i, p in enumerate(promises):
            p.then(resolver(i)).catch(lambda e: result_promise._reject(e))
        
        return result_promise
