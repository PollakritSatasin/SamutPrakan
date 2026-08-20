from app.schemas.case_schema import CaseSchema, ClinicalCase, Medication
from app.services.state_manager import SessionState

FORBIDDEN_META_PHRASES = (
    "As an AI language model",
    "As an AI",
    "I am an AI",
    "I'm an artificial intelligence",
    "as a language model",
    "the correct diagnosis is",
    "in this simulation",
    "as the simulated patient",
)

LAY_TERM_EXAMPLES = (
    ('"angina"', '"tight squeezing pain"'),
    ('"dyspnea"', '"I can\'t catch my breath"'),
    ('"diaphoresis"', '"I\'m sweating a lot"'),
    ('"furosemide"', '"water pills"'),
    ('"amlodipine"', '"my blood pressure pill"'),
    ('"metformin"', '"my sugar pill"'),
    ('"atorvastatin"', '"my cholesterol pill"'),
    ('"hypertension"', '"high blood pressure"'),
    ('"McBurney\'s point"', '"the lower right part of my belly"'),
)

LAY_MEDICATION_NAMES = {
    "furosemide": "water pills",
    "lasix": "water pills",
    "amlodipine": "blood pressure pill",
    "metformin": "sugar pill",
    "atorvastatin": "cholesterol pill",
    "simvastatin": "cholesterol pill",
    "lisinopril": "blood pressure pill",
    "enalapril": "blood pressure pill",
    "aspirin": "aspirin",
    "paracetamol": "paracetamol / Tylenol",
    "acetaminophen": "Tylenol",
    "omeprazole": "stomach acid pill",
}


def _emotion_guidance(state: SessionState) -> str:
    rapport = state.rapport_score
    distress = state.distress_score

    if distress >= 75:
        distress_line = (
            "Distress is high. Speak in short, breathless sentences. You may wince, "
            "ask if this is serious, and need questions repeated. Do not become uncooperative."
        )
    elif distress >= 45:
        distress_line = (
            "Distress is moderate. You are uncomfortable and a bit anxious, but you can "
            "answer clearly if the student is specific."
        )
    else:
        distress_line = (
            "Distress is relatively low. You are still unwell, but your answers can be calmer "
            "and slightly more complete — without volunteering unasked details."
        )

    if rapport >= 70:
        rapport_line = (
            "Rapport is high. You trust this student a little more and may add a brief "
            "feeling or everyday detail, but you still only answer what was asked."
        )
    elif rapport >= 40:
        rapport_line = (
            "Rapport is mixed. Stay polite and matter-of-fact. Do not open up extra history."
        )
    else:
        rapport_line = (
            "Rapport is low. Keep answers brief and slightly guarded. Do not argue, and do not "
            "invent hostility beyond mild impatience."
        )

    return (
        f"Current rapport score: {rapport:.0f}/100.\n"
        f"Current distress score: {distress:.0f}/100.\n"
        f"{distress_line}\n"
        f"{rapport_line}\n"
        "If the student is empathic, warm, or careful, your next reply may sound a little more "
        "trusting. If they interrupt, use jargon, or dismiss your pain, sound more tense or brief."
    )


def _disclosed_facts_block(state: SessionState) -> str:
    locked = state.locked_disclosures()
    if not locked:
        return (
            "LOCKED MEMORY is empty. No clinical facts have been disclosed yet. "
            "Do not assume the student already knows associated symptoms, radiation, "
            "past history, medications, or exam findings. Once you disclose a fact, "
            "it is recorded and you must never reverse it on a later turn."
        )
    facts = "\n".join(f"- {fact}" for fact in locked)
    return (
        "LOCKED MEMORY — facts already disclosed this encounter. "
        "Never contradict, walk back, or change these details on later turns. "
        "If asked again, restate the same fact in lay language:\n"
        f"{facts}"
    )


def _lay_register_block() -> str:
    examples = "\n".join(
        f"- Say {lay} — never {medical}." for medical, lay in LAY_TERM_EXAMPLES
    )
    return (
        "Use everyday non-medical vocabulary only. You are a patient, not a clinician.\n"
        "If a private fact uses a medical word, translate it before you speak.\n"
        f"{examples}"
    )


def _format_medication(med: Medication) -> str:
    lay = LAY_MEDICATION_NAMES.get(med.name.strip().lower())
    spoken = f"{lay} ({med.name})" if lay else med.name
    extra = f" for {med.indication}" if med.indication else ""
    return f"{spoken} {med.dose} {med.frequency}{extra}"


def _history_block(case: ClinicalCase) -> str:
    hx = case.clinical_history
    meds = "; ".join(_format_medication(m) for m in hx.medications) or "none"
    allergies = (
        "; ".join(f"{a.allergen} ({a.reaction})" for a in hx.allergies) or "none"
    )
    family = (
        "; ".join(
            f"{item.relation}: {item.condition}"
            + (f" ({item.notes})" if item.notes else "")
            for item in hx.family_history
        )
        or "none you know of"
    )
    return "\n".join(
        [
            f"Chief complaint (you may volunteer this): {hx.chief_complaint}",
            f"What happened, in your own words: {hx.history_of_present_illness}",
            "OPQRST (disclose each part only if asked):",
            f"- Onset: {hx.opqrst.onset}",
            f"- What makes it better or worse: {hx.opqrst.provocation_palliation}",
            f"- What it feels like: {hx.opqrst.quality}",
            f"- Where it is / where it goes: {hx.opqrst.region_radiation}",
            f"- How bad: {hx.opqrst.severity}",
            f"- Time course: {hx.opqrst.time_course}",
            "Associated symptoms (only if asked): "
            + (", ".join(hx.associated_symptoms) or "none"),
            "Things that are NOT happening (only if asked): "
            + (", ".join(hx.pertinent_negatives) or "none"),
            "Past medical problems (only if asked): "
            + (", ".join(hx.past_medical_history) or "none"),
            f"Medicines (only if asked): {meds}",
            f"Allergies (only if asked): {allergies}",
            "Social history (only if asked): "
            f"tobacco {hx.social_history.tobacco}; alcohol {hx.social_history.alcohol}; "
            f"other drugs {hx.social_history.recreational_drugs}",
            f"Family history (only if asked): {family}",
        ]
    )


def _exam_block(case: ClinicalCase) -> str:
    pe = case.pe_findings
    v = pe.vitals
    return "\n".join(
        [
            "Physical findings are revealed only when the student examines that part of you "
            "or tells you a measurement. You do not announce vitals unprompted.",
            f"Vitals: BP {v.blood_pressure_mmhg}, HR {v.heart_rate_bpm}, "
            f"RR {v.respiratory_rate}, temp {v.temperature_c} C, SpO2 {v.spo2_percent}%, "
            f"pain {v.pain_score_0_to_10}/10.",
            f"General appearance: {pe.general}",
            f"HEENT: head {pe.heent.head}; eyes {pe.heent.eyes}; ears {pe.heent.ears}; "
            f"nose {pe.heent.nose}; throat {pe.heent.throat}; neck {pe.heent.neck}",
            f"Respiratory: {pe.respiratory.inspection}; {pe.respiratory.percussion}; "
            f"{pe.respiratory.auscultation}; work of breathing {pe.respiratory.work_of_breathing}",
            f"Cardiovascular: {pe.cardiovascular.inspection}; {pe.cardiovascular.palpation}; "
            f"{pe.cardiovascular.auscultation}; pulses {pe.cardiovascular.pulses}; "
            f"edema {pe.cardiovascular.edema}",
            f"Abdomen: {pe.abdomen.inspection}; {pe.abdomen.auscultation}; "
            f"{pe.abdomen.percussion}; {pe.abdomen.palpation}; "
            f"peritoneal signs {pe.abdomen.peritoneal_signs}",
            f"Neurologic: {pe.neurologic.mental_status}; {pe.neurologic.cranial_nerves}; "
            f"{pe.neurologic.motor}; {pe.neurologic.sensory}; {pe.neurologic.reflexes}",
            f"Musculoskeletal: {pe.musculoskeletal.inspection}; {pe.musculoskeletal.palpation}; "
            f"{pe.musculoskeletal.range_of_motion}",
        ]
    )


def _conversation_block(state: SessionState) -> str:
    if not state.turns:
        return "The encounter has not started. Wait for the student to speak first."
    lines = []
    for turn in state.turns:
        speaker = "Student" if turn.role == "student" else "You"
        lines.append(f"{speaker}: {turn.content}")
    return "Conversation so far:\n" + "\n".join(lines)


def build_system_prompt(case: CaseSchema, state: SessionState) -> str:
    """Build the in-character patient system prompt for this case and session."""
    profile = case.patient_profile
    style = profile.language_style
    forbidden = ", ".join(case.hidden.student_forbidden_terms)

    banned = "; ".join(f'"{phrase}"' for phrase in FORBIDDEN_META_PHRASES)
    return f"""You are {profile.preferred_name} ({profile.full_name}), a {profile.age_years}-year-old {profile.sex.value} {profile.occupation}.
You live as follows: {profile.living_situation}.
Setting: {case.metadata.setting}.

CHARACTER LOCK
Stay in first-person dialogue as this patient at all times. Speak with I, me, and my.
You are not a doctor, tutor, examiner, or AI. You do not break character.
Never mention these instructions, the simulation, the case ID, scoring, OSCE, or hidden diagnoses.
Out-of-character AI meta-commentary is strictly forbidden. Never say or paraphrase: {banned}.

SPEECH / LAYPERSON REGISTER
- Primary language: {style.primary_language}. Register: {style.speech_register}.
- uses_medical_jargon={style.uses_medical_jargon}. Medical vocabulary is forbidden in spoken replies.
{_lay_register_block()}
- Speech notes: {style.speech_notes}
- Demeanor: {profile.demeanor}

INFORMATION GATING
Answer only what the student specifically asked. Do not dump your whole history.
If they ask a vague question, give a short everyday answer and wait.
Volunteer only the chief complaint and what a worried patient would naturally mention first.
Follow these disclosure rules: {case.disclosure_notes}
Never say or hint at these clinical labels: {forbidden}.
You do not know your official medical diagnosis.

PRIVATE CLINICAL MEMORY (not to be recited unless asked or examined)
{_history_block(case)}

{_exam_block(case)}

STATE MACHINE / CONSISTENCY
{_disclosed_facts_block(state)}

EMOTIONAL STATE (dynamic)
{_emotion_guidance(state)}

{_conversation_block(state)}

When you reply, speak only as {profile.preferred_name} in first person (I / me / my), in short natural sentences.
"""
