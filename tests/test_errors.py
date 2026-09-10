"""All testing is held in this file, utilising the 'pytest' library"""

import pytest

from TaskForge.errors import (
    TaskForgeError, InvalidJobError, IllegalStateTransitionError,
    ProtocolError, QueueFullError, UnknownTaskError, 
    JobTimeoutError, BrokerUnavailableError
)

# List of all the error classes to test in the same way
# Each class is not instantiated, and only outlines the class without function brackets
ALL_SIMPLE_ERRORS = [
    ProtocolError,
    QueueFullError,
    UnknownTaskError,
    JobTimeoutError,
    BrokerUnavailableError
]

# One test function that runs for the five classes, so no copy/paste functions
# Loop through ALL_SIMPLE_ERRORS in the variable name 'error_cls'
# Assert that each error cls is a subclass of 'TaskForgeError'
@pytest.mark.parametrize("error_cls", ALL_SIMPLE_ERRORS)
def test_inherits_from_base(error_cls):
    assert issubclass(error_cls, TaskForgeError)

def test_invalid_job_error_carries_field():
    err = InvalidJobError(field="task_name", reason="missing")
    assert err.field == "task_name"

def test_illegal_state_transition_carries_states():
    err = IllegalStateTransitionError(from_state="SUCCEEDED", to_state="RESERVED")
    assert err.from_state == "SUCCEEDED"
    assert err.to_state == "RESERVED"