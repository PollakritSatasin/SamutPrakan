from fastapi.testclient import TestClient


def test_list_cases(client: TestClient) -> None:
    response = client.get("/api/v1/cases")
    assert response.status_code == 200
    payload = response.json()
    assert {item["case_id"] for item in payload} == {
        "chest_pressure_walk_in",
        "migratory_abdominal_pain",
    }
    for item in payload:
        assert set(item) == {"case_id", "title", "chief_complaint", "setting"}
        assert "hidden" not in item
        assert "final_diagnosis" not in item


def test_get_case_overview_hides_diagnosis(client: TestClient) -> None:
    response = client.get("/api/v1/cases/chest_pressure_walk_in")
    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == "chest_pressure_walk_in"
    assert set(body) == {"case_id", "title", "chief_complaint", "setting"}
    blob = " ".join(str(v) for v in body.values()).lower()
    assert "nstemi" not in blob
    assert "acute coronary" not in blob
    assert "myocardial" not in blob


def test_get_unknown_case_404(client: TestClient) -> None:
    response = client.get("/api/v1/cases/not_a_real_case")
    assert response.status_code == 404


def test_create_and_complete_session(client: TestClient) -> None:
    created = client.post("/api/v1/sessions", json={"case_id": "chest_pressure_walk_in"})
    assert created.status_code == 201
    session = created.json()
    assert session["case_id"] == "chest_pressure_walk_in"
    assert session["status"] == "active"
    assert session["case"]["chief_complaint"]
    assert "final_diagnosis" not in session
    assert 0 <= session["rapport_score"] <= 100
    assert 0 <= session["distress_score"] <= 100

    session_id = session["session_id"]
    completed = client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={
            "turns": [
                {"role": "student", "content": "What is bothering you?"},
                {"role": "patient", "content": "My chest feels tight and heavy."},
            ]
        },
    )
    assert completed.status_code == 200
    body = completed.json()
    assert body["status"] == "completed"
    assert body["session_id"] == session_id
    assert len(body["transcript"]) == 2
    assert body["transcript"][1]["content"] == "My chest feels tight and heavy."
    assert "hidden" not in body

    again = client.post(f"/api/v1/sessions/{session_id}/complete")
    assert again.status_code == 409


def test_create_session_unknown_case(client: TestClient) -> None:
    response = client.post("/api/v1/sessions", json={"case_id": "missing"})
    assert response.status_code == 404


def test_complete_unknown_session(client: TestClient) -> None:
    response = client.post("/api/v1/sessions/00000000-0000-0000-0000-000000000000/complete")
    assert response.status_code == 404
