import sys
import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Ensure we can import from the parent backend folder
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, parse_a2ui_chunks

client = TestClient(app)

def test_parse_a2ui_chunks_text_only():
    text = "Hello, how can I help you today?"
    chunks = parse_a2ui_chunks(text)
    assert len(chunks) == 1
    assert chunks[0]["type"] == "text"
    assert chunks[0]["content"] == text

def test_parse_a2ui_chunks_with_markdown_block():
    text = "Here are your skills:\n```a2ui\n{\"data_view\": {\"layout\": \"grid\", \"items\": [{\"Skill\": \"Python\"}]}}\n```\nLet me know if you need move."
    chunks = parse_a2ui_chunks(text)
    
    assert len(chunks) == 3
    assert chunks[0]["type"] == "text"
    assert chunks[1]["type"] == "a2ui"
    assert chunks[1]["content"]["data_view"]["layout"] == "grid"
    assert "Python" in str(chunks[1]["content"])

def test_parse_a2ui_chunks_with_naked_json():
    text = "Sure! Here is the data: {\"data_view\": {\"text\": \"Metrics\"}}"
    chunks = parse_a2ui_chunks(text)
    
    assert len(chunks) == 2
    assert chunks[1]["type"] == "a2ui"
    assert chunks[1]["content"]["data_view"]["text"] == "Metrics"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

@patch("app.runner.run_async")
def test_chat_endpoint_mocked(mock_run):
    # Setup mock event
    mock_event = MagicMock()
    mock_event.is_final_response.return_value = True
    mock_event.content.parts = [MagicMock(text="Hello!")]
    
    async def mock_generator(*args, **kwargs):
        yield mock_event
        
    mock_run.return_value = mock_generator()
    
    # We need to provide an Origin that is in ALLOWED_ORIGINS_LIST 
    # for the strict_origin_middleware to pass
    response = client.post(
        "/chat",
        json={"message": "hi", "session_id": "test_session"},
        headers={"Origin": "http://localhost:5173"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "chunks" in data
    assert data["chunks"][0]["content"] == "Hello!"

def test_strict_origin_middleware_denies_unauthorized():
    response = client.post(
        "/chat",
        json={"message": "hi", "session_id": "test_session"},
        headers={"Origin": "https://hacking-site.com"}
    )
    assert response.status_code == 403
    assert "Access Denied" in response.json()["detail"]
