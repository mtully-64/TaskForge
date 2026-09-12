"""Testing for job.py, using pytest"""

import pytest

from TaskForge.job import JobState, TRANSITIONS

def test_pending_can_reach_reserved_state():
    # This should be an "in" operation and not "equals to"
    # As the reserved state is a member of the transition values, not a single item
    assert JobState.RESERVED in TRANSITIONS[JobState.PENDING]

def test_suceeded_is_terminal():
    assert TRANSITIONS[JobState.SUCCEEDED] == set()

def test_dead_reachable_from_reserved():
    assert JobState.DEAD in TRANSITIONS[JobState.RESERVED]

