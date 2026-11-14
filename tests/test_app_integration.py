"""
Test Suite for Master Application Integration.
Verifies clean imports, page registry integrity, and callable page renderers for the 6-page application.
"""

import pytest


def test_app_imports_and_page_registry():
    import app
    assert hasattr(app, "PAGES")
    assert len(app.PAGES) == 6, f"Expected 6 pages, found {len(app.PAGES)}"

    expected_pages = [
        "1. Overview & Architecture",
        "2. YouTube Data Collection",
        "3. Data Cleaning & Preprocessing",
        "4. Engagement Analytics",
        "5. Sentiment Analysis (Optional)",
        "6. Data Export & Reports",
    ]
    for p_name in expected_pages:
        assert p_name in app.PAGES, f"Missing page: {p_name}"
        assert callable(app.PAGES[p_name]), f"Page renderer for {p_name} is not callable."


def test_page_modules_direct_import():
    from src.ui.page_01_overview import render_page_overview
    from src.ui.page_02_collection import render_page_collection
    from src.ui.page_03_cleaning import render_page_cleaning
    from src.ui.page_04_engagement import render_page_engagement
    from src.ui.page_05_sentiment import render_page_sentiment
    from src.ui.page_06_exports import render_page_exports

    assert render_page_overview is not None
    assert render_page_collection is not None
    assert render_page_cleaning is not None
    assert render_page_engagement is not None
    assert render_page_sentiment is not None
    assert render_page_exports is not None
