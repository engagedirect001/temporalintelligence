"""
Task 22: Raft-like Consensus Log Replication
Category: Hardest — distributed systems + state machine + concurrency
"""
from enum import Enum, auto
from typing import List, Dict, Optional
import threading


class Role(Enum):
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()


class LogEntry:
    def __init__(self, term, command):
        self.term = term
        self.command = command
    
    def __eq__(self, other):
        return self.term == other.term and self.command == other.command
    
    def __repr__(self):
        return f"LogEntry(term={self.term}, cmd={self.command})"


class RaftNode:
    def __init__(self, node_id, cluster_size):
        self.node_id = node_id
        self.cluster_size = cluster_size
        
        # Persistent state
        self.current_term = 0
        self.voted_for = None
        self.log: List[LogEntry] = []
        
        # Volatile state
        self.commit_index = -1
        self.last_applied = -1
        self.role = Role.FOLLOWER
        
        # Leader state
        self.next_index: Dict[int, int] = {}
        self.match_index: Dict[int, int] = {}
        
        self.applied_commands = []
        self.lock = threading.Lock()
    
    def start_election(self):
        with self.lock:
            self.current_term += 1
            self.role = Role.CANDIDATE
            self.voted_for = self.node_id
            # Return vote request
            last_log_index = len(self.log) - 1
            last_log_term = self.log[-1].term if self.log else 0
            return {
                "term": self.current_term,
                "candidate_id": self.node_id,
                "last_log_index": last_log_index,
                "last_log_term": last_log_term,
            }
    
    def handle_vote_request(self, term, candidate_id, last_log_index, last_log_term):
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "vote_granted": False}
            
            if term > self.current_term:
                self.current_term = term
                self.role = Role.FOLLOWER
                self.voted_for = None
            
            # Check if we can vote for this candidate
            if self.voted_for is not None and self.voted_for != candidate_id:
                return {"term": self.current_term, "vote_granted": False}
            
            # Check log is at least as up-to-date
            my_last_term = self.log[-1].term if self.log else 0
            my_last_index = len(self.log) - 1
            
            # Bug 1: log comparison is wrong — should check term first,
            # then index only if terms are equal
            log_ok = (last_log_index >= my_last_index and last_log_term >= my_last_term)
            
            if log_ok:
                self.voted_for = candidate_id
                return {"term": self.current_term, "vote_granted": True}
            
            return {"term": self.current_term, "vote_granted": False}
    
    def become_leader(self):
        with self.lock:
            self.role = Role.LEADER
            # Initialize leader state
            for i in range(self.cluster_size):
                if i != self.node_id:
                    # Bug 2: next_index should be len(self.log), not len(self.log) - 1
                    self.next_index[i] = len(self.log) - 1
                    self.match_index[i] = -1
    
    def append_entry(self, command):
        """Leader appends a new command."""
        with self.lock:
            if self.role != Role.LEADER:
                raise RuntimeError("Not leader")
            entry = LogEntry(self.current_term, command)
            self.log.append(entry)
            return len(self.log) - 1
    
    def prepare_append_entries(self, follower_id):
        """Prepare AppendEntries RPC for a follower."""
        with self.lock:
            next_idx = self.next_index.get(follower_id, 0)
            prev_log_index = next_idx - 1
            prev_log_term = self.log[prev_log_index].term if prev_log_index >= 0 and prev_log_index < len(self.log) else 0
            
            entries = self.log[next_idx:]
            
            return {
                "term": self.current_term,
                "leader_id": self.node_id,
                "prev_log_index": prev_log_index,
                "prev_log_term": prev_log_term,
                "entries": entries,
                "leader_commit": self.commit_index,
            }
    
    def handle_append_entries(self, term, leader_id, prev_log_index, prev_log_term,
                               entries, leader_commit):
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "success": False}
            
            self.current_term = term
            self.role = Role.FOLLOWER
            
            # Check prev log consistency
            if prev_log_index >= 0:
                if prev_log_index >= len(self.log):
                    return {"term": self.current_term, "success": False}
                if self.log[prev_log_index].term != prev_log_term:
                    # Delete conflicting entries
                    self.log = self.log[:prev_log_index]
                    return {"term": self.current_term, "success": False}
            
            # Append new entries
            for i, entry in enumerate(entries):
                idx = prev_log_index + 1 + i
                if idx < len(self.log):
                    if self.log[idx].term != entry.term:
                        self.log = self.log[:idx]
                        self.log.append(entry)
                    # else: already have this entry
                else:
                    self.log.append(entry)
            
            # Bug 3: commit index update is wrong — should be min of leader_commit
            # and index of last NEW entry, not just leader_commit
            if leader_commit > self.commit_index:
                self.commit_index = leader_commit
            
            self._apply_committed()
            return {"term": self.current_term, "success": True}
    
    def handle_append_response(self, follower_id, success, entries_sent):
        with self.lock:
            if success:
                self.next_index[follower_id] = self.next_index.get(follower_id, 0) + len(entries_sent)
                self.match_index[follower_id] = self.next_index[follower_id] - 1
                self._update_commit_index()
            else:
                self.next_index[follower_id] = max(0, self.next_index.get(follower_id, 1) - 1)
    
    def _update_commit_index(self):
        """Leader updates commit_index based on majority replication."""
        for n in range(len(self.log) - 1, self.commit_index, -1):
            if self.log[n].term != self.current_term:
                continue
            replication_count = 1  # self
            for fid in self.match_index:
                if self.match_index[fid] >= n:
                    replication_count += 1
            if replication_count > self.cluster_size // 2:
                self.commit_index = n
                self._apply_committed()
                break
    
    def _apply_committed(self):
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            if self.last_applied < len(self.log):
                self.applied_commands.append(self.log[self.last_applied].command)
