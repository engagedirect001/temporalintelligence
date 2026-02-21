import pytest
from buggy_code import Elevator, Direction, DoorState


def test_simple_up():
    e = Elevator(10)
    e.request_floor(5)
    stops = e.run_until_idle()
    assert 5 in stops


def test_multiple_stops_same_direction():
    e = Elevator(10)
    e.request_floor(3)
    e.request_floor(5)
    e.request_floor(7)
    stops = e.run_until_idle()
    assert 3 in stops and 5 in stops and 7 in stops


def test_direction_reversal_picks_up_requests():
    """Bug 1: When reversing, should pick up requests in new direction at current floor."""
    e = Elevator(10)
    e.current_floor = 5
    
    # Someone at floor 7 wants to go DOWN
    e.request_floor(7, Direction.DOWN)
    # Someone inside wants floor 7
    e.request_floor(7)
    
    stops = e.run_until_idle()
    assert 7 in stops


def test_dont_clear_wrong_direction_request():
    """Bug 2: Stopping while going UP should not clear DOWN request at same floor."""
    e = Elevator(10)
    e.current_floor = 1
    
    # Floor 5: UP request and DOWN request
    e.request_floor(5, Direction.UP)
    e.request_floor(5, Direction.DOWN)
    # Someone inside wants floor 8
    e.request_floor(8)
    
    stops = e.run_until_idle()
    
    # Going up: should stop at 5 (UP request), continue to 8
    # Then coming back down: should stop at 5 again (DOWN request)
    count_5 = stops.count(5)
    assert count_5 == 2, \
        f"Floor 5 should be visited twice (up and down), but visited {count_5} times. Stops: {stops}"


def test_reversal_checks_current_floor():
    """Bug 3: When reversing direction, should check current floor before moving."""
    e = Elevator(10)
    e.current_floor = 5
    
    # Request at floor 3 going up
    e.request_floor(3, Direction.UP)
    # Request at floor 5 from cabin (current floor)
    e.request_floor(5)
    
    # Should stop at 5 first (already there), then go down to 3
    stops = e.run_until_idle()
    assert stops[0] == 5, f"Should stop at current floor 5 first, but stops={stops}"


def test_idle_when_no_requests():
    e = Elevator(10)
    result = e.step()
    assert result is None
    assert e.direction == Direction.IDLE


def test_door_opens_and_closes():
    e = Elevator(10)
    e.request_floor(2)
    
    # Step until we reach floor 2
    for _ in range(20):
        result = e.step()
        if result is None:
            break
    
    assert 2 in e.stops
