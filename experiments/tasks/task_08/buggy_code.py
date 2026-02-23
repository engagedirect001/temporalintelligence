"""
Task 08: Interval Merge with Weighted Selection
Category: Algorithm bugs (merge + binary search)
"""

def merge_intervals(intervals):
    """Merge overlapping intervals. Each interval is (start, end, weight).
    When merging, weights are summed."""
    if not intervals:
        return []
    
    # Bug 1: sorts by start only, but should be stable sort —
    # when starts are equal, should sort by end DESCENDING to handle containment
    sorted_ivs = sorted(intervals, key=lambda x: x[0])
    
    merged = [list(sorted_ivs[0])]
    
    for start, end, weight in sorted_ivs[1:]:
        # Bug 2: uses > instead of >= for overlap check
        # Adjacent intervals like (1,3) and (3,5) should merge
        if start > merged[-1][1]:
            merged.append([start, end, weight])
        else:
            merged[-1][1] = max(merged[-1][1], end)
            merged[-1][2] += weight
    
    return [tuple(m) for m in merged]


def find_interval(merged, point):
    """Binary search for the interval containing a point."""
    lo, hi = 0, len(merged) - 1
    
    while lo <= hi:
        mid = (lo + hi) // 2
        start, end, weight = merged[mid]
        
        if point < start:
            hi = mid - 1
        # Bug 3: uses < instead of <= for end comparison
        # so point == end is not found
        elif point < end:
            return merged[mid]
        else:
            lo = mid + 1
    
    return None


def weighted_coverage(intervals):
    """Return total coverage length, weighted by overlap count."""
    merged = merge_intervals(intervals)
    return sum((end - start) * weight for start, end, weight in merged)
