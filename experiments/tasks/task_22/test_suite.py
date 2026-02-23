import pytest
from buggy_code import RaftNode, Role, LogEntry


def test_election_basic():
    node = RaftNode(0, 3)
    req = node.start_election()
    assert req["term"] == 1
    assert node.role == Role.CANDIDATE


def test_vote_grant():
    voter = RaftNode(1, 3)
    resp = voter.handle_vote_request(term=1, candidate_id=0,
                                      last_log_index=-1, last_log_term=0)
    assert resp["vote_granted"] is True


def test_log_up_to_date_check():
    """Bug 1: Log comparison should prioritize term over index."""
    voter = RaftNode(1, 3)
    # Voter has a short log but with higher term
    voter.log = [LogEntry(1, "a"), LogEntry(3, "b")]  # last term=3, index=1
    voter.current_term = 3
    
    # Candidate has longer log but lower last term
    resp = voter.handle_vote_request(
        term=4, candidate_id=0,
        last_log_index=5,  # longer
        last_log_term=2     # but lower term
    )
    assert resp["vote_granted"] is False, \
        "Should reject candidate with lower last log term even if longer log"


def test_leader_next_index_init():
    """Bug 2: next_index should be initialized to len(log), not len(log)-1."""
    leader = RaftNode(0, 3)
    leader.log = [LogEntry(1, "a"), LogEntry(1, "b"), LogEntry(1, "c")]
    leader.current_term = 1
    leader.become_leader()
    
    # next_index should be 3 (next slot after last entry)
    for fid in leader.next_index:
        assert leader.next_index[fid] == 3, \
            f"next_index[{fid}] = {leader.next_index[fid]}, expected 3"


def test_append_entries_basic():
    leader = RaftNode(0, 3)
    leader.become_leader()
    leader.current_term = 1
    
    idx = leader.append_entry("set x=1")
    assert idx == 0
    assert len(leader.log) == 1


def test_follower_append():
    follower = RaftNode(1, 3)
    entries = [LogEntry(1, "set x=1")]
    
    resp = follower.handle_append_entries(
        term=1, leader_id=0,
        prev_log_index=-1, prev_log_term=0,
        entries=entries, leader_commit=-1
    )
    assert resp["success"] is True
    assert len(follower.log) == 1


def test_commit_index_safety():
    """Bug 3: follower commit_index should not exceed its actual log length."""
    follower = RaftNode(1, 3)
    
    # Follower has 1 entry
    entries = [LogEntry(1, "cmd1")]
    follower.handle_append_entries(
        term=1, leader_id=0,
        prev_log_index=-1, prev_log_term=0,
        entries=entries, leader_commit=-1
    )
    
    # Leader says commit_index=5 but follower only has 1 entry
    follower.handle_append_entries(
        term=1, leader_id=0,
        prev_log_index=0, prev_log_term=1,
        entries=[], leader_commit=5
    )
    
    # Follower should not apply entries it doesn't have
    assert follower.commit_index <= len(follower.log) - 1, \
        f"commit_index={follower.commit_index} but log has {len(follower.log)} entries"


def test_full_replication_flow():
    """End-to-end: leader replicates to follower, commits, follower applies."""
    leader = RaftNode(0, 3)
    follower1 = RaftNode(1, 3)
    follower2 = RaftNode(2, 3)
    
    leader.become_leader()
    leader.current_term = 1
    
    leader.append_entry("set x=1")
    
    # Replicate to follower1
    msg = leader.prepare_append_entries(1)
    resp = follower1.handle_append_entries(**msg)
    assert resp["success"] is True
    
    leader.handle_append_response(1, True, msg["entries"])
    
    # After majority (leader + follower1), should commit
    assert leader.commit_index == 0
    assert "set x=1" in leader.applied_commands
