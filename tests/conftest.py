

# DEFAULT_REFERENCE_MUSEUM_PROFILE_FOR_TESTS
import pytest


@pytest.fixture(autouse=True)
def _reference_museum_profile_for_tests(monkeypatch):
    """
    Tests that need a runnable reference configuration explicitly use the
    shipped Stadtmuseum Berlin reference profile.

    Production code deliberately has no implicit museum-profile default.
    Individual tests may delete or override MUSEUM_PROFILE when testing
    configuration errors or alternative profiles.
    """
    monkeypatch.setenv("MUSEUM_PROFILE", "stadtmuseum-berlin")
    monkeypatch.setenv("PRESIGN_URL", "http://127.0.0.1:18082/s3/presign")
