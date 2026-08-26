import os, tempfile
os.environ["DATABASE_URL"] = "sqlite:///./test_unibot.db"
os.environ["JWT_SECRET"] = "test-secret"
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
def auth(email="test@example.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secure-password"})
    return {"Authorization": "Bearer " + client.post("/api/auth/login", json={"email": email, "password": "secure-password"}).json()["access_token"]}
def test_user_data_is_isolated():
    a, b = auth(), auth("other@example.com")
    payload = {"title":"Placement CV", "content":{"summary":"Python developer", "personal":{}, "experiences":[], "projects":[], "skills":[]}}
    r = client.post("/api/resumes", json=payload, headers=a); assert r.status_code == 201
    assert client.get("/api/resumes", headers=b).json() == []
def test_ats_returns_explainable_result():
    h=auth("ats@example.com"); r=client.post("/api/resumes", headers=h, json={"content":{"summary":"Built Python APIs", "personal":{}, "experiences":[{"bullets":["Built API that reduced latency 30%"]}], "projects":[], "skills":[{"items":["Python", "FastAPI"]}]}}).json()
    report=client.post(f"/api/resumes/{r['id']}/ats", headers=h, json={"job_description":"Python FastAPI engineer building API systems with Docker and SQL experience."}).json()
    assert 0 <= report["score"] <= 100 and "missing_keywords" in report
def test_resume_command_adds_postgresql_to_skills():
    h=auth("command@example.com")
    r=client.post("/api/resumes", headers=h, json={"content":{"raw_text":"Aman Kumar\n\nSKILLS\nPython, FastAPI","personal":{},"summary":"","experiences":[],"projects":[],"skills":[]}}).json()
    proposal=client.post(f"/api/resumes/{r['id']}/command", headers=h, json={"instruction":"Add PostgreSQL to skills","raw_text":"Aman Kumar\n\nSKILLS\nPython, FastAPI"})
    assert proposal.status_code == 200 and proposal.json()["status"] == "proposal"
    result=client.post(f"/api/resumes/{r['id']}/command", headers=h, json={"instruction":"Add PostgreSQL to skills","raw_text":"Aman Kumar\n\nSKILLS\nPython, FastAPI","confirm":True,"proposed_text":proposal.json()["proposed_text"]})
    assert result.status_code == 200 and "PostgreSQL" in result.json()["raw_text"]

def test_vague_edit_requests_clarification():
    h=auth("clarify@example.com")
    r=client.post("/api/resumes", headers=h, json={"content":{"raw_text":"Built Python APIs"}}).json()
    result=client.post(f"/api/resumes/{r['id']}/selection-edit", headers=h, json={"selected_text":"Built Python APIs","instruction":"Improve it"})
    assert result.json()["status"] == "needs_clarification"
