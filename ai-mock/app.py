from __future__ import annotations

from pathlib import Path
import json

from fastapi import FastAPI, HTTPException


app = FastAPI(title="Deterministic AI Mock")
_FIXTURES = Path(__file__).parent / "fixtures"
_OPERATIONS = {
    "extract_found_item": "extraction_umbrella.json",
    "generate_questions": "questions_umbrella.json",
    "verify_answers": "verification_match.json",
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
def chat_completion(payload: dict[str, object]) -> dict[str, object]:
    operation = str(payload.get("operation", ""))
    fixture_name = _OPERATIONS.get(operation)
    if fixture_name is None:
        raise HTTPException(status_code=400, detail="MOCK_OPERATION_UNKNOWN")
    fixture = json.loads((_FIXTURES / fixture_name).read_text(encoding="utf-8"))
    return {"choices": [{"message": {"content": json.dumps(fixture, ensure_ascii=False)}}]}
