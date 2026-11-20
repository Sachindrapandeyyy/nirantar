import pytest
from core.stealth import STEALTH_EVASION_JS


def test_stealth_js_signatures():
    assert "webdriver" in STEALTH_EVASION_JS
    assert "window.chrome" in STEALTH_EVASION_JS
    assert "languages" in STEALTH_EVASION_JS
    assert "hardwareConcurrency" in STEALTH_EVASION_JS
