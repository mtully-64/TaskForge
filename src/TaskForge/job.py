from enum import StrEnum
from dataclasses import dataclass, field
import time
from TaskForge.ulid import generate_ulid
from TaskForge.errors import IllegalStateTransitionError

class JobState(StrEnum):
    """
    Job lifecycle states.
    Enumeration was used via strings. Where a special class is made, to create a set of named constraints.
    """
    # Sitting in the queue, eligible or waiting for its scheduled time
    PENDING = "pending"
    # Handed to a worker, now holding a lease on it
    # Not yet finished
    RESERVED = "reserved"
    # The worker ran it and it returned normally
    SUCCEEDED = "succeeded"
    # The worker ran it and it raised, but it has retries left
    # It will go back to pending (this is like a transient state really)
    FAILED = "failed"
    # It failed and has no retries left
    # It is in the dead-letter queue (DLQ - a specialised holding sub-queue where a messaging system stores messages it can't deliver)
    DEAD = "dead"
    # Human or API killed it before it ran
    CANCELLED = "cancelled"

"""
Module/file level dictionary mapping (written at module level and not a class attribute)
Where each state is mapped to a set of states in which it may legally move to.
"""   
TRANSITIONS = {
    JobState.PENDING: {JobState.RESERVED, JobState.CANCELLED},
    JobState.RESERVED: {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED, JobState.DEAD},
    JobState.DEAD: {JobState.PENDING},
    JobState.FAILED: {JobState.PENDING},
    # Empty set means that it is done
    JobState.SUCCEEDED: set(),
    JobState.CANCELLED: set(),
}

@dataclass(kw_only=True)
class Job:
    """
    This is a dataclass, with everything the system needs to know about one unit of work
    This object:
        - Gets created by a producer, serialised, sent over a socket, written to a log file on disk, read back after a crash,
            sent to a worker on another machine, and possibly all of that twice if the first worker dies.
        - Hence, every field must survive a round trip and ensure that they mean the same thing on both sides
    """

    ############################
    # Identity
    ############################

    # Unique for each value, including the encoding of the creation time, meaning the sorting can be chronologically ordered by time
    job_id: str = field(default_factory=generate_ulid) # Universal Unique Lexicographically Identifier

    ############################
    # Routing
    ############################

    # Outlines which queue the job belongs to
    queue_name: str = "default"
    # The registered name of the function to run, not the function itself
    # The function does not exist on the broker, only on the worker
    #   - The broker never knows what a job does, and moves opaque payloads around
    #   - Only the worker knows how to execute them
    task_name: str

    ############################
    # Payload
    ############################

    # Positional arguments
    args: list = field(default_factory=list)
    # Keyword arguments
    kwargs: dict = field(default_factory=dict)

    ############################
    # Retry Policy
    ############################

    # Number of times to retry after the first failure 
    max_retries: int = 3    # Celery does one attempt plus the three retries, so four in total
    # How many times it has been tried before
    attempt: int = 0

    ############################
    # Timing
    ############################

    # Epoch seconds
    created_at: float = field(default_factory=time.time)
    # Epoch seconds
    # Defaults to created_at in post initialise
    # None must be declared, as just 'float' would mean the kw is required to be supplied still after "kw_only=True"
    scheduled_for: float | None = None
    # How long a worker may spend on it before being killed
    # No job can eternally block a worker slot
    timeout_seconds: float = 30 # 30 seconds

    ############################
    # Priority
    ############################

    # Used to order the jobs
    # Unix nice and Celery use a lower number to reflect higher urgency (handier for heap comparison I think)
    priority: int = 5

    ############################
    # State
    ############################

    # Job is to start in the pending state
    state:JobState = JobState.PENDING

    ############################
    # Idempotency
    ############################  
      
    # Used to deduplicate enqueue requests
    # A repeat within the window returns the original job ID instead of creating a duplicate
    idempotency_key: str | None = None

    ############################
    # Failure Diagnostics
    ############################    
    
    # Populated on failure, so the Dead-Letter Queue can show why something died without needing a seperate lookup
    last_error: str | None = None

    ############################
    # Tracing
    ############################    

    # Correlation ID generated at enqueued carried through logs across every process this job touches
    trace_id: str | None = None

    def is_eligible(self, now: float) -> bool:
        """
        Returns whether this job may be handed to a worker at time 'now'
        This means that the state is 'pending' and the 'scheduled_for' is less than or equal to 'now'
        """
        if self.state == JobState.PENDING and self.scheduled_for <= now:
            return True
        else:
            return False

    def transition_to(self, new_state: JobState) -> None:
        """
        Transition table is checked and raises 'IllegalStateTransitionError' if the move is not permitted
        Otherwise, the self.state is set to this state
        """
        if new_state not in TRANSITIONS[self.state]:
            raise IllegalStateTransitionError(self.state, new_state)
        else:
            self.state = new_state

    def __repr__(self):
        """
        Need to ensure that its readable in the log
        """
        # 8 chars for the job id is enough to view
        truncated_id = self.job_id[0:8]
        return f'Job({truncated_id}, {self.task_name}, queue={self.queue_name}, state={self.state.value}, attempt={self.attempt}/{self.max_retries})'

    def __post_init__(self):
        """
        The __post_init__ special method is called by __init__ as its very last step, after every field has been set up from whatever has been passed
        The 'field(default_factory=)' only allows me to call the function, with no args, to get a default
        Therefore, I need a way to compute a field's value from another field on the same instance, given there's no instance yet
        """
        # __init__ runs first, sets the created_at field to a time and scheduled_for is set to None
        # I cannot set scheduled_for to created_at within a dataclass, as at class definition time 'created_at' isn't a value yet
        # Then in __post_init__ the 'self.created_at' is copied into self.scheduled_for
        if self.scheduled_for is None:
            self.scheduled_for = self.created_at