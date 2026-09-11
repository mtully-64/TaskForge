"""
This file contains my exception classes.
Nothing else in the project will raise a bare 'Exception' or 'ValueError' from this point onwards.

This means that when a broker catches an error, it needs to decide: 
- Is this a bad client that I should reject and keep serving?, or, is this my own corrupted state and should I shut down?

It cannot make that decision solely from the pre-existing 'except Exception', the only way to make the decision is typed errors.
Also, when you write 'except ValueError' around a block, you then catch not only the validation error intended to be caught,
but also a 'ValueError' raised accidentally by int() three frames deeper.

Purposely there is no inheriting from 'ValueError' or 'TypeError', this brings all the ambiguity I am trying to rid.
"""

class TaskForgeError(Exception):
    """Base class that inherits Exception, then every other error will inherit TaskForgeError"""

class InvalidJobError(TaskForgeError):
    """A job could not be built from the data given"""
    def __init__(self, field, reason):
        # Additional information is needed in an attribute - allowing to understand what field failed and why
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid job: field '{field}' - {reason}")

class IllegalStateTransitionError(TaskForgeError):
    """The state machine forbid the movement of a job between 2 states"""
    def __init__(self, from_state, to_state):
        # Additional information is needed to carry more information about the error, then just a string
        # Hence, the 2 relevant states need to be accounted for
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Illegal state transition: from '{from_state}' to '{to_state}'")

class ProtocolError(TaskForgeError):
    """A frame received over the wire was malformed"""

class QueueFullError(TaskForgeError):
    """An enqueue was rejected due to the queue hitting its depth limit"""

class UnknownTaskError(TaskForgeError):
    """A worker received a job naming a task that it has no handler registered for"""

class JobTimeoutError(TaskForgeError):
    """A job exceeded its allowed runtime and was killed"""

class BrokerUnavailableError(TaskForgeError):
    """A client could not reach any broker after retrying"""