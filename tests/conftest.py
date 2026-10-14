import os
import tempfile

# Use a throw-away database so tests never touch real data. Must be set before backend imports.
_tmp = tempfile.mkdtemp()
os.environ["RESUME_DB"] = os.path.join(_tmp, "test.db")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    from backend.services import upload_service
    monkeypatch.setattr(upload_service, "UPLOAD_DIR", tmp_path / "uploads")
