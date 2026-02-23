"""
Task 04: TCP Connection State Machine
Category: State machine bugs
"""
from enum import Enum, auto


class TCPState(Enum):
    CLOSED = auto()
    LISTEN = auto()
    SYN_SENT = auto()
    SYN_RECEIVED = auto()
    ESTABLISHED = auto()
    FIN_WAIT_1 = auto()
    FIN_WAIT_2 = auto()
    CLOSE_WAIT = auto()
    CLOSING = auto()
    LAST_ACK = auto()
    TIME_WAIT = auto()


class TCPConnection:
    def __init__(self):
        self.state = TCPState.CLOSED
        self.send_buffer = []
        self.recv_buffer = []
        self._error = None
    
    def listen(self):
        if self.state != TCPState.CLOSED:
            raise ConnectionError(f"Cannot listen in state {self.state}")
        self.state = TCPState.LISTEN
    
    def connect(self):
        if self.state != TCPState.CLOSED:
            raise ConnectionError(f"Cannot connect in state {self.state}")
        self.state = TCPState.SYN_SENT
    
    def receive_syn(self):
        if self.state == TCPState.LISTEN:
            self.state = TCPState.SYN_RECEIVED
        elif self.state == TCPState.SYN_SENT:
            # Simultaneous open
            self.state = TCPState.SYN_RECEIVED
        else:
            raise ConnectionError(f"Unexpected SYN in state {self.state}")
    
    def receive_syn_ack(self):
        if self.state == TCPState.SYN_SENT:
            self.state = TCPState.ESTABLISHED
        else:
            raise ConnectionError(f"Unexpected SYN-ACK in state {self.state}")
    
    def receive_ack(self):
        if self.state == TCPState.SYN_RECEIVED:
            self.state = TCPState.ESTABLISHED
        elif self.state == TCPState.FIN_WAIT_1:
            self.state = TCPState.FIN_WAIT_2
        elif self.state == TCPState.CLOSING:
            self.state = TCPState.TIME_WAIT
        # Bug 1: Missing transition — LAST_ACK + ACK should go to CLOSED
        # (omitted entirely)
        elif self.state == TCPState.ESTABLISHED:
            pass  # data ACK, stay
        else:
            raise ConnectionError(f"Unexpected ACK in state {self.state}")
    
    def close(self):
        if self.state == TCPState.ESTABLISHED:
            self.state = TCPState.FIN_WAIT_1
        elif self.state == TCPState.CLOSE_WAIT:
            self.state = TCPState.LAST_ACK
        # Bug 2: Missing LISTEN -> CLOSED transition
        else:
            raise ConnectionError(f"Cannot close in state {self.state}")
    
    def receive_fin(self):
        if self.state == TCPState.ESTABLISHED:
            self.state = TCPState.CLOSE_WAIT
        elif self.state == TCPState.FIN_WAIT_1:
            # Bug 3: Goes to TIME_WAIT instead of CLOSING
            # (TIME_WAIT should only happen after FIN_WAIT_2 receives FIN)
            self.state = TCPState.TIME_WAIT
        elif self.state == TCPState.FIN_WAIT_2:
            self.state = TCPState.TIME_WAIT
        else:
            raise ConnectionError(f"Unexpected FIN in state {self.state}")
    
    def send_data(self, data):
        if self.state != TCPState.ESTABLISHED:
            raise ConnectionError(f"Cannot send in state {self.state}")
        self.send_buffer.append(data)
    
    def timeout(self):
        """Handle TIME_WAIT timeout."""
        if self.state == TCPState.TIME_WAIT:
            self.state = TCPState.CLOSED
