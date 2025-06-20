import pytest
import sys
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def app():
    """Session-wide QApplication fixture for all Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app 