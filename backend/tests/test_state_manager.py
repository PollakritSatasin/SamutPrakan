import pytest

from app.services.state_manager import SessionManager, SessionState, clamp_score


def test_session_state_tracks_turns_and_disclosed_facts() -> None:
    state = SessionState("chest_pressure_walk_in")
    state.add_turn("student", "What brought you in today?")
    state.add_turn(
        "patient",
        "My chest feels tight.",
        disclosed_facts=["chief_complaint:chest_tightness"],
    )

    assert len(state.turns) == 2
    assert state.turns[0].role == "student"
    assert state.has_disclosed("chief_complaint:chest_tightness")
    assert "chief_complaint:chest_tightness" in state.disclosed_facts
    assert state.transcript()[1].content == "My chest feels tight."


def test_session_memory_keeps_disclosed_items_across_turns() -> None:
    state = SessionState("chest_pressure_walk_in")
    state.add_turn(
        "patient",
        "It started while I was walking.",
        disclosed_facts=["onset:while_walking"],
    )
    state.remember("quality:tight_squeezing")
    state.add_turn("student", "Does rest help?")
    state.add_turn(
        "patient",
        "No, sitting has not helped.",
        disclosed_facts=["palliation:rest_no_help"],
    )

    locked = state.locked_disclosures()
    assert state.has_disclosed("onset:while_walking")
    assert state.has_disclosed("quality:tight_squeezing")
    assert state.has_disclosed("palliation:rest_no_help")
    assert "It started while I was walking." in locked
    assert locked == sorted(locked)
    assert state.disclose("onset:while_walking") is False


def test_rapport_and_distress_are_ephemeral_and_clamped() -> None:
    state = SessionState("chest_pressure_walk_in", rapport_score=50, distress_score=70)
    assert state.adjust_rapport(80) == 100.0
    assert state.adjust_distress(-100) == 0.0
    assert clamp_score(140) == 100.0
    assert clamp_score(-5) == 0.0


def test_completed_session_rejects_new_turns() -> None:
    state = SessionState("chest_pressure_walk_in")
    state.complete()
    with pytest.raises(ValueError, match="completed session"):
        state.add_turn("student", "Hello")
    with pytest.raises(ValueError, match="already completed"):
        state.complete()


def test_session_manager_create_get_and_complete() -> None:
    manager = SessionManager()
    created = manager.create("migratory_abdominal_pain")
    fetched = manager.get(created.session_id)
    assert fetched is created
    completed = manager.complete(created.session_id)
    assert completed.status == "completed"
    assert completed.completed_at is not None
