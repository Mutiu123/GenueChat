"""Tests for src.config."""

import pytest

from src.config import Environment, Settings, get_settings


class TestSettings:
    def test_default_app_name(self, settings):
        assert settings.APP_NAME == "GenueChat"

    def test_environment_is_development(self, settings):
        assert settings.ENVIRONMENT == Environment.DEVELOPMENT

    def test_is_development_property(self, settings):
        assert settings.is_development is True

    def test_is_production_false_in_dev(self, settings):
        assert settings.is_production is False

    def test_cors_origins_list(self, settings):
        origins = settings.cors_origins_list
        assert isinstance(origins, list)
        assert len(origins) >= 1

    def test_cors_origins_validation_empty_raises(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "")
        get_settings.cache_clear()
        with pytest.raises(Exception):
            Settings(CORS_ORIGINS="")

    def test_get_settings_caching(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
