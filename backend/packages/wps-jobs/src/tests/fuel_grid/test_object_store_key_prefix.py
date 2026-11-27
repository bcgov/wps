"""OBJECT_STORE_KEY_PREFIX coverage for jobs key builders."""

from fuel_grid.install import get_fuel_masked_tpi_key_for_version


def test_jobs_keys_unchanged_when_prefix_unset(monkeypatch):
    monkeypatch.delenv("OBJECT_STORE_KEY_PREFIX", raising=False)
    monkeypatch.setenv("CLASSIFIED_TPI_DEM_NAME", "bc_dem_50m_tpi_win100_classified.tif")
    assert (
        get_fuel_masked_tpi_key_for_version(2024, 3)
        == "dem/tpi/bc_dem_50m_tpi_win100_classified_fuel_masked_2024_v3.tif"
    )


def test_jobs_keys_prefixed_when_set(monkeypatch):
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", "local/tester")
    monkeypatch.setenv("CLASSIFIED_TPI_DEM_NAME", "bc_dem_50m_tpi_win100_classified.tif")
    assert (
        get_fuel_masked_tpi_key_for_version(2024, 3)
        == "local/tester/dem/tpi/bc_dem_50m_tpi_win100_classified_fuel_masked_2024_v3.tif"
    )


def test_jobs_keys_normalize_trailing_slash(monkeypatch):
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", "local/tester/")
    monkeypatch.setenv("CLASSIFIED_TPI_DEM_NAME", "bc_dem_50m_tpi_win100_classified.tif")
    assert (
        get_fuel_masked_tpi_key_for_version(2024, 3)
        == "local/tester/dem/tpi/bc_dem_50m_tpi_win100_classified_fuel_masked_2024_v3.tif"
    )
