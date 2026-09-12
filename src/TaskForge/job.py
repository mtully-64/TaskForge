from enum import StrEnum

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