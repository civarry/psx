import pytest
import shutil
import tempfile
from pathlib import Path

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output and clean it up afterwards"""
    temp_dir = tempfile.mkdtemp(prefix="test_output_")
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_company_config():
    """Return a sample company configuration"""
    return {
        "company_name": "TEST COMPANY INC.",
        "footer_text": "Test Footer Text",
        "document_id": "TEST-ID-001",
        "effectivity_date": "January 1, 2025"
    }

@pytest.fixture
def sample_logo_path(tmp_path):
    """Create a dummy logo file"""
    logo = tmp_path / "logo.png"
    # Create a 1x1 dummy image or just empty file since we might mock the image reader
    # But for reportlab to not crash if it tries to open it, we might need a valid image or mock
    # For now, let's create a tiny valid PNG to be safe
    # 1x1 pixel red png
    with open(logo, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8e\x06\x00\x00\x00\x00IEND\xaeB`\x82')
    return str(logo)
