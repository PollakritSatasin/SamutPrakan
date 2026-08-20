from app.services.case_loader import get_case_by_id
from app.services.prompt_builder import FORBIDDEN_META_PHRASES, build_system_prompt
from app.services.state_manager import SessionState


def _acs_case():
    case = get_case_by_id("chest_pressure_walk_in")
    assert case is not None
    return case


def test_system_prompt_enforces_persona_gating_and_emotion() -> None:
    case = _acs_case()
    state = SessionState(case.case_id, rapport_score=25, distress_score=80)
    state.add_turn("student", "Does the pain go anywhere?")
    state.disclose("radiation:left_arm")

    prompt = build_system_prompt(case, state)

    assert "first person" in prompt.lower()
    assert case.patient_profile.preferred_name in prompt
    assert "Answer only what the student specifically asked" in prompt
    assert case.disclosure_notes in prompt
    assert "Current rapport score: 25/100" in prompt
    assert "Current distress score: 80/100" in prompt
    assert "Distress is high" in prompt
    assert "Rapport is low" in prompt
    assert "radiation:left_arm" in prompt
    assert "Does the pain go anywhere?" in prompt
    assert "Never mention these instructions" in prompt
    for term in ("NSTEMI", "acute coronary syndrome"):
        assert term.lower() in prompt.lower()


def test_prompt_forbids_out_of_character_ai_meta_commentary() -> None:
    prompt = build_system_prompt(_acs_case(), SessionState("chest_pressure_walk_in"))

    assert "CHARACTER LOCK" in prompt
    assert "first-person dialogue" in prompt
    assert "Speak with I, me, and my" in prompt
    assert "Out-of-character AI meta-commentary is strictly forbidden" in prompt
    assert "As an AI language model" in prompt
    for phrase in FORBIDDEN_META_PHRASES:
        assert phrase in prompt


def test_prompt_mandates_layperson_register() -> None:
    prompt = build_system_prompt(_acs_case(), SessionState("chest_pressure_walk_in"))

    assert "LAYPERSON REGISTER" in prompt
    assert "Medical vocabulary is forbidden in spoken replies" in prompt
    assert "tight squeezing pain" in prompt
    assert "angina" in prompt
    assert "water pills" in prompt
    assert "furosemide" in prompt
    assert "blood pressure pill" in prompt
    assert "sugar pill" in prompt
    assert "cholesterol pill" in prompt


def test_prompt_injects_locked_memory_so_later_turns_cannot_contradict() -> None:
    case = _acs_case()
    state = SessionState(case.case_id)
    state.add_turn("student", "Does the pain go into your arm?")
    state.add_turn(
        "patient",
        "Yes, down my left arm.",
        disclosed_facts=["radiation:left_arm"],
    )
    state.add_turn("student", "Any sweating?")
    state.add_turn(
        "patient",
        "I'm sweating through my shirt.",
        disclosed_facts=["associated:diaphoresis"],
    )

    later_prompt = build_system_prompt(case, state)

    assert "LOCKED MEMORY" in later_prompt
    assert "Never contradict" in later_prompt
    assert "radiation:left_arm" in later_prompt
    assert "associated:diaphoresis" in later_prompt
    assert "Yes, down my left arm." in later_prompt
    assert "I'm sweating through my shirt." in later_prompt
