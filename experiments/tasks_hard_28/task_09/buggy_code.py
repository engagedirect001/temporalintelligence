"""
Task 09: Async Task Scheduler with Dependencies
Category: Concurrency bugs (async patterns)
"""
import asyncio
from collections import defaultdict


class AsyncTaskScheduler:
    """Schedule async tasks respecting dependency ordering."""
    
    def __init__(self):
        self.tasks = {}  # name -> coroutine factory
        self.deps = defaultdict(set)  # name -> set of dependency names
        self.results = {}
        self.completed = set()
        self._events = {}  # name -> asyncio.Event
        self.execution_order = []
    
    def add_task(self, name, coro_fn, dependencies=None):
        self.tasks[name] = coro_fn
        if dependencies:
            self.deps[name] = set(dependencies)
        self._events[name] = asyncio.Event()
    
    async def _run_task(self, name):
        # Wait for all dependencies
        for dep in self.deps.get(name, set()):
            if dep not in self._events:
                raise ValueError(f"Unknown dependency: {dep}")
            await self._events[dep].wait()
        
        # Gather dependency results
        dep_results = {d: self.results.get(d) for d in self.deps.get(name, set())}
        
        # Execute
        # Bug 1: doesn't handle exceptions — if a task fails, dependents wait forever
        result = await self.tasks[name](dep_results)
        
        self.results[name] = result
        self.execution_order.append(name)
        self.completed.add(name)
        self._events[name].set()
    
    async def run_all(self, timeout=None):
        """Run all tasks respecting dependencies."""
        # Bug 2: doesn't detect cycles — will deadlock on circular deps
        tasks = [self._run_task(name) for name in self.tasks]
        
        # Bug 3: asyncio.gather without return_exceptions means first exception
        # cancels everything, but we don't handle CancelledError in _run_task
        await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=timeout
        )
        
        return self.results
    
    def has_cycle(self):
        """Check for dependency cycles using DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            for dep in self.deps.get(node, set()):
                if dep not in visited:
                    if dfs(dep):
                        return True
                # Bug in cycle detection: should check rec_stack, not visited
                elif dep in visited:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.tasks:
            if node not in visited:
                if dfs(node):
                    return True
        return False
