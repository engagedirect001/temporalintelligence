"""
Task 26: HTTP/2-like Stream Multiplexer
Category: Hardest — protocol + concurrency + state machine
"""
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import threading


class StreamState(Enum):
    IDLE = auto()
    OPEN = auto()
    HALF_CLOSED_LOCAL = auto()
    HALF_CLOSED_REMOTE = auto()
    CLOSED = auto()


class Frame:
    def __init__(self, stream_id: int, frame_type: str, data: bytes = b"",
                 flags: set = None, priority: int = 16):
        self.stream_id = stream_id
        self.frame_type = frame_type  # HEADERS, DATA, RST_STREAM, WINDOW_UPDATE, END_STREAM
        self.data = data
        self.flags = flags or set()
        self.priority = priority


class Stream:
    def __init__(self, stream_id: int, window_size: int = 65535):
        self.stream_id = stream_id
        self.state = StreamState.IDLE
        self.send_window = window_size
        self.recv_window = window_size
        self.recv_buffer = b""
        self.priority = 16
    
    def is_writable(self):
        return self.state in (StreamState.OPEN, StreamState.HALF_CLOSED_REMOTE)
    
    def is_readable(self):
        return self.state in (StreamState.OPEN, StreamState.HALF_CLOSED_LOCAL)


class StreamMultiplexer:
    """HTTP/2-like stream multiplexer with flow control."""
    
    def __init__(self, initial_window=65535):
        self.streams: Dict[int, Stream] = {}
        self.initial_window = initial_window
        self.connection_window = initial_window
        self.next_stream_id = 1
        self.lock = threading.Lock()
        self.outbound_queue: List[Frame] = []
        self.errors: List[str] = []
    
    def create_stream(self, priority=16) -> int:
        with self.lock:
            sid = self.next_stream_id
            # Bug 1: HTTP/2 client streams must be odd-numbered
            # but we increment by 1 instead of 2
            self.next_stream_id += 1
            stream = Stream(sid, self.initial_window)
            stream.priority = priority
            stream.state = StreamState.OPEN
            self.streams[sid] = stream
            return sid
    
    def send_headers(self, stream_id: int, headers: dict, end_stream=False):
        with self.lock:
            stream = self._get_stream(stream_id)
            if stream.state not in (StreamState.IDLE, StreamState.OPEN):
                self.errors.append(f"Cannot send headers in state {stream.state}")
                return False
            
            flags = set()
            if end_stream:
                flags.add("END_STREAM")
                # Bug 2: should transition to HALF_CLOSED_LOCAL, not CLOSED
                stream.state = StreamState.CLOSED
            else:
                stream.state = StreamState.OPEN
            
            self.outbound_queue.append(Frame(stream_id, "HEADERS", 
                                             str(headers).encode(), flags))
            return True
    
    def send_data(self, stream_id: int, data: bytes, end_stream=False):
        with self.lock:
            stream = self._get_stream(stream_id)
            
            if not stream.is_writable():
                self.errors.append(f"Stream {stream_id} not writable")
                return False
            
            # Flow control
            # Bug 3: checks stream window but not connection window
            if len(data) > stream.send_window:
                self.errors.append(f"Exceeds stream flow control window")
                return False
            
            stream.send_window -= len(data)
            self.connection_window -= len(data)
            
            flags = set()
            if end_stream:
                flags.add("END_STREAM")
                if stream.state == StreamState.OPEN:
                    stream.state = StreamState.HALF_CLOSED_LOCAL
                elif stream.state == StreamState.HALF_CLOSED_REMOTE:
                    stream.state = StreamState.CLOSED
            
            self.outbound_queue.append(Frame(stream_id, "DATA", data, flags))
            return True
    
    def receive_frame(self, frame: Frame):
        with self.lock:
            if frame.stream_id not in self.streams:
                if frame.frame_type == "HEADERS":
                    self.streams[frame.stream_id] = Stream(frame.stream_id, self.initial_window)
                    self.streams[frame.stream_id].state = StreamState.OPEN
                else:
                    self.errors.append(f"Frame for unknown stream {frame.stream_id}")
                    return
            
            stream = self.streams[frame.stream_id]
            
            if frame.frame_type == "DATA":
                if not stream.is_readable():
                    self.errors.append(f"Stream {frame.stream_id} not readable")
                    return
                stream.recv_buffer += frame.data
                stream.recv_window -= len(frame.data)
            
            if frame.frame_type == "WINDOW_UPDATE":
                delta = int.from_bytes(frame.data[:4], 'big') if frame.data else 0
                stream.send_window += delta
                return
            
            if "END_STREAM" in frame.flags:
                if stream.state == StreamState.OPEN:
                    stream.state = StreamState.HALF_CLOSED_REMOTE
                elif stream.state == StreamState.HALF_CLOSED_LOCAL:
                    stream.state = StreamState.CLOSED
            
            if frame.frame_type == "RST_STREAM":
                stream.state = StreamState.CLOSED
    
    def _get_stream(self, stream_id):
        if stream_id not in self.streams:
            raise KeyError(f"Unknown stream {stream_id}")
        return self.streams[stream_id]
    
    def get_prioritized_queue(self):
        """Return outbound frames sorted by stream priority (lower = higher priority)."""
        return sorted(self.outbound_queue, key=lambda f: 
                      self.streams.get(f.stream_id, Stream(0)).priority)
