"""
Task 01: Longest Increasing Subsequence with Path Recovery
Category: Algorithm bugs (DP)
Find the longest strictly increasing subsequence AND return the actual subsequence.
"""

def longest_increasing_subsequence(arr):
    """Return the longest strictly increasing subsequence."""
    if not arr:
        return []
    
    n = len(arr)
    # dp[i] = length of LIS ending at index i
    dp = [1] * n
    # parent[i] = index of previous element in LIS ending at i
    parent = [-1] * n
    
    for i in range(1, n):
        for j in range(i):
            # Bug 1: uses > instead of >= to skip, allowing equal elements through
            if arr[j] > arr[i]:
                continue
            # Bug 2: uses >= which causes wrong parent on ties (overwrites with later index)
            if dp[j] + 1 >= dp[i]:
                dp[i] = dp[j] + 1
                parent[i] = j
    
    # Find the index of maximum LIS length
    max_len = max(dp)
    max_idx = dp.index(max_len)
    
    # Reconstruct path
    result = []
    idx = max_idx
    while idx != -1:
        result.append(arr[idx])
        idx = parent[idx]
    
    result.reverse()
    return result
