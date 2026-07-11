"""Tests for file operations: upload, raw download, binary detection"""
import io
import shutil
import time
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.knowledge.service import create_knowledge
from app.main import app
from app.files.service import (
    is_binary_file,
    get_binary_content,
    upload_file,
    BINARY_EXTENSIONS,
)


def _force_rmtree(path: Path):
    if not path.exists():
        return
    for _ in range(3):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            time.sleep(0.1)
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def setup_test_kb(tmp_path):
    import uuid

    kb_id = f"file-test-{uuid.uuid4().hex[:8]}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
    try:
        create_knowledge(kb_id, f"File测试库-{kb_id}", "用于文件操作测试", ["test"], "tester")
        yield kb_id, kb_path
    finally:
        _force_rmtree(kb_path)


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
async def auth_token(client: AsyncClient):
    import uuid
    unique = uuid.uuid4().hex[:8]
    resp = await client.post(
        "/api/auth/register",
        json={
            "username": f"file_test_user_{unique}",
            "email": f"file_{unique}@test.com",
            "password": "test123",
        },
    )
    if resp.status_code != 200:
        # User might exist, just login
        pass
    resp = await client.post(
        "/api/auth/login",
        json={"username": f"file_test_user_{unique}", "password": "test123"},
    )
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ========== Binary Detection Tests ==========


class TestBinaryDetection:
    def test_binary_extension_png(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        # Create a fake PNG file
        png_path = kb_path / "test.png"
        png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        assert is_binary_file(f"{kb_id}/test.png") is True

    def test_binary_extension_pdf(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        pdf_path = kb_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4" + b"\x00" * 100)
        assert is_binary_file(f"{kb_id}/test.pdf") is True

    def test_text_file_not_binary(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        txt_path = kb_path / "test.md"
        txt_path.write_text("# Hello World\nThis is text.", encoding="utf-8")
        assert is_binary_file(f"{kb_id}/test.md") is False

    def test_python_file_not_binary(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        py_path = kb_path / "test.py"
        py_path.write_text("print('hello')", encoding="utf-8")
        assert is_binary_file(f"{kb_id}/test.py") is False

    def test_binary_content_detection(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        # File with non-UTF8 bytes
        bin_path = kb_path / "data.bin"
        bin_path.write_bytes(bytes(range(256)))
        assert is_binary_file(f"{kb_id}/data.bin") is True


# ========== Upload Tests ==========


class TestUpload:
    def test_upload_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        content = b"Hello, this is test content"
        result = upload_file(kb_id, "uploaded.txt", content)
        assert result is True
        assert (kb_path / "uploaded.txt").exists()
        assert (kb_path / "uploaded.txt").read_bytes() == content

    def test_upload_creates_dirs(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        content = b"nested content"
        result = upload_file(kb_id, "subdir/nested/file.txt", content)
        assert result is True
        assert (kb_path / "subdir/nested/file.txt").exists()

    def test_upload_binary_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        content = bytes(range(256)) * 100
        result = upload_file(kb_id, "image.png", content)
        assert result is True
        assert (kb_path / "image.png").read_bytes() == content


# ========== Raw Content Tests ==========


class TestRawContent:
    def test_get_binary_content(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        (kb_path / "test.png").write_bytes(content)
        result = get_binary_content(kb_id, "test.png")
        assert result == content

    def test_get_text_as_binary(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        content = "Hello World".encode("utf-8")
        (kb_path / "test.txt").write_bytes(content)
        result = get_binary_content(kb_id, "test.txt")
        assert result == content

    def test_get_nonexistent_file(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = get_binary_content(kb_id, "nonexistent.png")
        assert result is None

    def test_get_directory_as_binary(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        (kb_path / "subdir").mkdir()
        result = get_binary_content(kb_id, "subdir")
        assert result is None


# ========== API Upload Tests ==========


@pytest.mark.anyio
async def test_upload_api(client: AsyncClient, setup_test_kb, auth_token: str):
    kb_id, kb_path = setup_test_kb
    file_content = b"Test upload content"
    resp = await client.post(
        f"/api/knowledge/{kb_id}/files/upload",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        headers=auth_header(auth_token),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "上传成功"
    assert (kb_path / "test.txt").exists()


@pytest.mark.anyio
async def test_upload_api_with_path(client: AsyncClient, setup_test_kb, auth_token: str):
    kb_id, kb_path = setup_test_kb
    file_content = b"Nested upload"
    resp = await client.post(
        f"/api/knowledge/{kb_id}/files/upload?path=docs",
        files={"file": ("readme.md", io.BytesIO(file_content), "text/markdown")},
        headers=auth_header(auth_token),
    )
    assert resp.status_code == 200
    assert (kb_path / "docs" / "readme.md").exists()


@pytest.mark.anyio
async def test_raw_file_api(client: AsyncClient, setup_test_kb, auth_token: str):
    kb_id, kb_path = setup_test_kb
    content = b"\x89PNG\r\n" + b"\x00" * 50
    (kb_path / "image.png").write_bytes(content)

    resp = await client.get(
        f"/api/knowledge/{kb_id}/files/image.png/raw",
        headers=auth_header(auth_token),
    )
    assert resp.status_code == 200
    assert resp.content == content
    assert "image/png" in resp.headers["content-type"]


@pytest.mark.anyio
async def test_raw_file_not_found(client: AsyncClient, setup_test_kb, auth_token: str):
    kb_id, _ = setup_test_kb
    resp = await client.get(
        f"/api/knowledge/{kb_id}/files/nonexistent.png/raw",
        headers=auth_header(auth_token),
    )
    assert resp.status_code == 404


# ========== BINARY_EXTENSIONS constant tests ==========


class TestBinaryExtensions:
    def test_has_common_image_extensions(self):
        assert "png" in BINARY_EXTENSIONS
        assert "jpg" in BINARY_EXTENSIONS
        assert "gif" in BINARY_EXTENSIONS

    def test_has_document_extensions(self):
        assert "pdf" in BINARY_EXTENSIONS
        assert "docx" in BINARY_EXTENSIONS
        assert "xlsx" in BINARY_EXTENSIONS

    def test_does_not_have_text_extensions(self):
        assert "md" not in BINARY_EXTENSIONS
        assert "py" not in BINARY_EXTENSIONS
        assert "js" not in BINARY_EXTENSIONS
        assert "txt" not in BINARY_EXTENSIONS
