from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.db import reset_engine
from app.main import app
from app.services.state_manager import SessionManager


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    reset_engine(url=f"sqlite:///{tmp_path / 'test.db'}")
    app.state.session_manager = SessionManager()
    with TestClient(app) as test_client:
        yield test_client
    app.state.session_manager = SessionManager()
