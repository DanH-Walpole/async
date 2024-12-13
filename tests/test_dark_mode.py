import pytest
from src.searchapp.web.dash_app import toggle_theme

def test_toggle_theme_initial():
    """Test initial theme state"""
    result = toggle_theme(None, None)
    assert result == {"theme": "light"}, "Initial theme should be light"

def test_toggle_theme_to_dark():
    """Test toggling from light to dark theme"""
    result = toggle_theme(1, {"theme": "light"})
    assert result == {"theme": "dark"}, "Theme should switch to dark"

def test_toggle_theme_to_light():
    """Test toggling from dark to light theme"""
    result = toggle_theme(1, {"theme": "dark"})
    assert result == {"theme": "light"}, "Theme should switch to light"

def test_toggle_theme_with_invalid_state():
    """Test toggling with invalid/missing state"""
    result = toggle_theme(1, None)
    assert result == {"theme": "dark"}, "Invalid state should default to dark"
