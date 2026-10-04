"""Testing for job.py, using pytest"""

import pytest

from TaskForge.job import Job, JobState, TRANSITIONS
from TaskForge.errors import IllegalStateTransitionError

def test_pending_can_reach_reserved_state():
    # This should be an "in" operation and not "equals to"
    # As the reserved state is a member of the transition values, not a single item
    assert JobState.RESERVED in TRANSITIONS[JobState.PENDING]

def test_succeeded_is_terminal():
    assert TRANSITIONS[JobState.SUCCEEDED] == set()

def test_dead_reachable_from_reserved():
    assert JobState.DEAD in TRANSITIONS[JobState.RESERVED]

def test_defaults():
    job = Job(task_name="x")
    assert job.state == JobState.PENDING
    assert job.attempt == 0
    assert job.max_retries == 3
    assert job.queue_name == "default"
    assert job.priority == 5
    assert job.args == []
    assert job.kwargs == {}
    assert job.idempotency_key is None
    assert job.last_error is None
    assert job.trace_id is None


def test_scheduled_for_defaults_to_created_at():
    job = Job(task_name="x")
    assert job.scheduled_for == job.created_at


def test_explicit_scheduled_for_is_kept():
    job = Job(task_name="x", scheduled_for=12345.0)
    assert job.scheduled_for == 12345.0


def test_job_ids_are_unique():
    ids = {Job(task_name="x").job_id for _ in range(100)}
    assert len(ids) == 100


def test_args_and_kwargs_are_not_shared():
    a = Job(task_name="x")
    b = Job(task_name="x")
    a.args.append(1)
    a.kwargs["k"] = "v"
    assert b.args == []
    assert b.kwargs == {}


def test_not_eligible_when_scheduled_in_future():
    job = Job(task_name="x", scheduled_for=100.0)
    assert job.is_eligible(now=50.0) is False


def test_eligible_when_scheduled_in_past():
    job = Job(task_name="x", scheduled_for=100.0)
    assert job.is_eligible(now=150.0) is True


def test_not_eligible_when_not_pending():
    job = Job(task_name="x", scheduled_for=100.0, state=JobState.RESERVED)
    assert job.is_eligible(now=150.0) is False

def test_eligible_when_scheduled_exactly_now():
    job = Job(task_name="x", scheduled_for=100.0)
    assert job.is_eligible(now=100.0) is True
    
@pytest.mark.parametrize("start, target", [
    (JobState.PENDING, JobState.RESERVED),
    (JobState.PENDING, JobState.CANCELLED),
    (JobState.RESERVED, JobState.SUCCEEDED),
    (JobState.RESERVED, JobState.FAILED),
    (JobState.FAILED, JobState.PENDING),
    (JobState.DEAD, JobState.PENDING),
])
def test_legal_transitions(start, target):
    job = Job(task_name="x", state=start)
    job.transition_to(target)
    assert job.state == target


@pytest.mark.parametrize("start, target", [
    (JobState.PENDING, JobState.SUCCEEDED),
    (JobState.PENDING, JobState.PENDING),
    (JobState.PENDING, JobState.DEAD),
    (JobState.SUCCEEDED, JobState.PENDING),
    (JobState.SUCCEEDED, JobState.RESERVED),
    (JobState.CANCELLED, JobState.PENDING),
])
def test_illegal_transitions_raise_and_leave_state_unchanged(start, target):
    job = Job(task_name="x", state=start)
    with pytest.raises(IllegalStateTransitionError):
        job.transition_to(target)
    assert job.state == start


def test_illegal_transition_carries_both_states():
    job = Job(task_name="x", state=JobState.SUCCEEDED)
    with pytest.raises(IllegalStateTransitionError) as exc_info:
        job.transition_to(JobState.RESERVED)
    assert exc_info.value.from_state == JobState.SUCCEEDED
    assert exc_info.value.to_state == JobState.RESERVED


def test_repr_is_readable_and_does_not_crash():
    job = Job(task_name="send_email", queue_name="email")
    text = repr(job)
    assert "send_email" in text
    assert "queue=email" in text
    assert "attempt=0/3" in text
    assert job.job_id[:8] in text