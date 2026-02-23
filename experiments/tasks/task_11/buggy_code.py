"""
Task 11: Elevator State Machine with Multiple Floors
Category: State machine bugs
"""
from enum import Enum, auto


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    IDLE = auto()


class DoorState(Enum):
    OPEN = auto()
    CLOSED = auto()


class Elevator:
    def __init__(self, num_floors=10):
        self.num_floors = num_floors
        self.current_floor = 1
        self.direction = Direction.IDLE
        self.door = DoorState.CLOSED
        self.requests_up = set()    # floors with UP button pressed
        self.requests_down = set()  # floors with DOWN button pressed
        self.cabin_requests = set() # floors requested from inside
        self.stops = []  # log of floors stopped at
    
    def request_floor(self, floor, direction=None):
        """External request: someone at `floor` wants to go `direction`."""
        if floor < 1 or floor > self.num_floors:
            raise ValueError(f"Invalid floor {floor}")
        if direction == Direction.UP:
            self.requests_up.add(floor)
        elif direction == Direction.DOWN:
            self.requests_down.add(floor)
        else:
            self.cabin_requests.add(floor)
    
    def _has_requests_above(self):
        all_requests = self.requests_up | self.requests_down | self.cabin_requests
        return any(f > self.current_floor for f in all_requests)
    
    def _has_requests_below(self):
        all_requests = self.requests_up | self.requests_down | self.cabin_requests
        return any(f < self.current_floor for f in all_requests)
    
    def _should_stop(self):
        """Determine if elevator should stop at current floor."""
        if self.current_floor in self.cabin_requests:
            return True
        if self.direction == Direction.UP and self.current_floor in self.requests_up:
            return True
        if self.direction == Direction.DOWN and self.current_floor in self.requests_down:
            return True
        # Bug 1: Doesn't stop for opposite-direction requests when about to reverse
        # e.g., going UP but no more UP requests above — should pick up DOWN requests
        return False
    
    def _clear_current_requests(self):
        self.cabin_requests.discard(self.current_floor)
        # Bug 2: Always clears both up AND down requests at current floor
        # Should only clear the request matching current direction
        self.requests_up.discard(self.current_floor)
        self.requests_down.discard(self.current_floor)
    
    def step(self):
        """Execute one step of the elevator algorithm. Returns current floor or None if idle."""
        if self.door == DoorState.OPEN:
            self.door = DoorState.CLOSED
            return self.current_floor
        
        # Determine direction
        if self.direction == Direction.IDLE:
            if self._has_requests_above():
                self.direction = Direction.UP
            elif self._has_requests_below():
                self.direction = Direction.DOWN
            else:
                return None  # nothing to do
        
        # Move
        if self.direction == Direction.UP:
            if self._has_requests_above():
                self.current_floor += 1
            else:
                # Bug 3: switches to DOWN but doesn't check current floor first
                self.direction = Direction.DOWN
                self.current_floor -= 1
        elif self.direction == Direction.DOWN:
            if self._has_requests_below():
                self.current_floor -= 1
            else:
                self.direction = Direction.UP
                self.current_floor += 1
        
        # Check if should stop
        if self._should_stop():
            self.door = DoorState.OPEN
            self._clear_current_requests()
            self.stops.append(self.current_floor)
        
        return self.current_floor
    
    def run_until_idle(self, max_steps=100):
        """Run until no more requests."""
        steps = 0
        while steps < max_steps:
            result = self.step()
            if result is None:
                break
            steps += 1
        return self.stops
