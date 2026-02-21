# TEMPORAL Condition — Accumulated Pattern Memory

## Algorithm Bugs (Tasks 1-9, prior patterns)
- **LIS path recovery**: Track predecessors during DP, reconstruct path backwards
- **B-Tree split indexing**: Median index calculation off-by-one in odd-sized nodes
- **Interval merge boundaries**: Sort by start, merge when overlap (<=, not <)
- **Robin Hood hashing**: Probe distance comparison must account for wraparound

## State Machine Bugs (Tasks 10-15, prior patterns)
- **TCP transitions**: CLOSE_WAIT→LAST_ACK on active close from FIN_WAIT states
- **Elevator direction**: Don't reverse until no more requests in current direction
- **Circuit breaker half-open**: Single success → CLOSED, single failure → OPEN
- **Raft log comparison**: Compare term FIRST, then index only if terms equal (Task 22 reinforced)

## Concurrency Bugs (Tasks 16-19, prior patterns)
- **Bounded buffer conditions**: Signal correct condition (not_empty vs not_full)
- **Async failure propagation**: Await all tasks, don't swallow exceptions
- **Priority queue timeouts**: Use monotonic clock, handle spurious wakeups
- **Ring buffer modular math**: Use `% capacity` not `& mask` for non-power-of-2 (Task 23 reinforced)

## Math/Numerical (Tasks 20-21, prior patterns)
- **Welford's variance**: Divide by (n-1) for sample variance, not n
- **Kalman filter covariance**: Update ALL matrix elements in update step; process noise scales with dt (Task 27 reinforced)
- **RSA totient**: φ(n) = (p-1)(q-1), not p*q-1
- **Matrix inverse sign**: Cofactor sign alternation (-1)^(i+j)

## System Design (Tasks 22-28, new patterns)
- **Raft leader init**: next_index = len(log), not len(log)-1; commit_index bounded by log length
- **SPSC ring buffer**: Use modulo for non-power-of-2 capacity; _size = (head-tail) % capacity
- **Skip list delete**: Only update forward[i] if it actually points to target node at level i
- **Skip list range_query**: Use `<=` for inclusive end bound
- **Event sourcing snapshots**: Deep copy snapshots to prevent mutation; handle compacted state correctly
- **Event sourcing compact**: After pruning events, snapshot key must remain reachable by rebuild logic
- **HTTP/2 streams**: Client stream IDs increment by 2 (odd only); END_STREAM on headers → HALF_CLOSED_LOCAL, not CLOSED
- **HTTP/2 flow control**: Check BOTH stream window AND connection window before sending
- **Kalman filter**: Update all 4 covariance elements: P[2] = p10 - K1*p00, P[3] = p11 - K1*p01
- **MVCC visibility**: Skip uncommitted versions (continue, don't break) when scanning for visible version
- **MVCC serializable**: Validate read-set at commit — reject if any read key was written by another committed txn since start_ts

## Meta-Patterns
- **Off-by-one in initialization**: Leader state, buffer capacity, index bounds
- **Incomplete state updates**: Covariance matrices, forward pointers at all levels
- **Wrong comparison operators**: < vs <=, >= vs >
- **Missing validation**: Version ordering, connection-level flow control, read-set validation
- **Shallow vs deep copy**: Snapshots, cached state that gets mutated later
- **Break vs continue**: In search loops, breaking on non-match loses older valid entries

## Task 20 Note
Task 20 has a bad test asserting 2^10 mod 1000 = 1024 (mathematically impossible). Code was fixed correctly; 1 test fails due to bad assertion. This is expected.
