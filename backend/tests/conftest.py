import os
import shutil
import tempfile
from pathlib import Path

# Override DATABASE_URL for testing BEFORE importing application modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
import app.db.database as db_module
from app.db.database import Base, get_db

# Create SQLite in-memory test engine with StaticPool so all connections share the same memory DB
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database module engine
db_module.engine = engine

@pytest.fixture(scope="session", autouse=True)
def temp_upload_dir():
    """Create a temporary directory for file storage during testing."""
    temp_dir = Path(tempfile.mkdtemp())
    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = temp_dir
    yield temp_dir
    # Cleanup after test suite finishes
    shutil.rmtree(temp_dir, ignore_errors=True)
    settings.UPLOAD_DIR = original_upload_dir

@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden database session."""
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
