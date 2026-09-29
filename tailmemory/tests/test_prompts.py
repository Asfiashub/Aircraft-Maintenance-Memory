from app.agent.prompts import diagnosis_system_prompt, diagnosis_user_prompt


def test_prompt_requires_evidence_boundary():
    system_prompt = diagnosis_system_prompt()
    assert "Never invent maintenance history" in system_prompt
    assert "previously failed" in system_prompt


def test_empty_memory_prompt_is_explicit():
    prompt = diagnosis_user_prompt("VT-XYZ", "Hydraulic warning", [])
    assert "RECALLED HINDSIGHT MEMORIES" in prompt
    assert "[]" in prompt