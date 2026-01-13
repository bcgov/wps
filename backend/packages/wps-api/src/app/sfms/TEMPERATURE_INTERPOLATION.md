# SFMS Temperature Interpolation

Implementation of station-based temperature interpolation using Inverse Distance Weighting (IDW) with elevation adjustment for the SFMS (Satellite Fire Monitoring System) Insights project.

## Overview

This feature interpolates temperature observations from weather stations to a continuous raster surface using IDW interpolation with elevation correction. The implementation follows the methodology specified in issue [#4995](https://github.com/bcgov/wps/issues/4995) and builds upon the requirements from [#4962](https://github.com/bcgov/wps/issues/4962).

## Methodology

### 1. Data Acquisition
- Fetches noon observation data from WF1 (Wildfire One) API
- Uses **all stations** that have valid temperature and elevation values
- Filters to ACTUAL observations only (not forecasts)

### 2. Temperature Normalization to Sea Level
Each station temperature is adjusted to sea level (0m elevation) using the **dry adiabatic lapse rate**:

```
T_sea_level = T_station + (elevation_m × 0.0098°C/m)
```

Where:
- Dry adiabatic lapse rate = 9.8°C per 1000m = 0.0098°C per meter
- This accounts for atmospheric temperature decrease with elevation gain

**Example:**
- Station at 1000m elevation with 10°C temperature
- Sea level temperature = 10 + (1000 × 0.0098) = 19.8°C

### 3. Inverse Distance Weighting (IDW) Interpolation

For each raster cell, the sea level temperature is interpolated from nearby stations using IDW:

```
T_interpolated = Σ(w_i × T_i) / Σ(w_i)

where: w_i = 1 / (distance_i ^ power)
```

**Parameters:**
- **Power parameter**: 2.0 (standard IDW)
- **Search radius**: 200 km (200,000 meters)
- **Distance calculation**: Haversine formula for great circle distance

**Edge Cases:**
- If target point is within 1m of a station, use that station's value directly
- If no stations within search radius, cell is marked as NoData

### 4. Elevation Adjustment to Terrain

The interpolated sea level temperature is adjusted back to actual terrain elevation using the DEM:

```
T_final = T_sea_level - (elevation_DEM × 0.0098°C/m)
```

This produces the final temperature at the actual surface elevation.

## Implementation

### Core Modules

#### 0. `wps_shared.geospatial.spatial_interpolation`
**Shared spatial interpolation utilities** - reusable across all weather parameter interpolation.

**Functions:**
- `haversine_distance()`: Great circle distance calculation between lat/lon points
- `idw_interpolation()`: Generic IDW interpolation for any spatial data
  - Fully decoupled from domain models
  - Works with simple lists of coordinates and values
  - Configurable power parameter and search radius

**Constants:**
- `IDW_POWER = 2.0`: Standard IDW power parameter
- `SEARCH_RADIUS = 200000`: Default 200km search radius in meters

**Location:** `packages/wps-shared/src/wps_shared/geospatial/spatial_interpolation.py`

**Reusability:** This module can be used for interpolating:
- Temperature (current implementation)
- Dew point temperature
- Wind speed
- Precipitation
- Any other spatially distributed point data

#### 1. `wps_shared.sfms.raster_addresser.RasterKeyAddresser`
**Central S3 key management** - provides consistent path generation for all SFMS rasters.

**Methods:**
- `get_interpolated_key(datetime_utc, weather_param)`: Generates S3 keys for interpolated weather parameter rasters
  - Format: `sfms/interpolated/{param}/YYYY/MM/DD/{param}_YYYYMMDD.tif`
  - Parameters:
    - `datetime_utc`: UTC datetime for the raster (validated with `assert_all_utc()`)
    - `weather_param`: `WeatherParameter` enum (TEMP, RH, or WIND_SPEED)
  - Examples:
    - Temperature: `sfms/interpolated/temp/2024/01/15/temp_20240115.tif`
    - Relative Humidity: `sfms/interpolated/rh/2024/01/15/rh_20240115.tif`
    - Wind Speed: `sfms/interpolated/wind_speed/2024/01/15/wind_speed_20240115.tif`
  - Follows the same pattern as other SFMS raster keys (fuel, indices, etc.)

**Location:** `packages/wps-shared/src/wps_shared/sfms/raster_addresser.py`

**Reusability:** This method is fully generic and can be used for any weather parameter in the `WeatherParameter` enum without modification.

#### 2. `wps_shared.schemas.sfms.StationTemperature`
Pydantic data model for station temperature data.

**Fields:**
- `code: int` - Station code
- `lat: float` - Latitude in degrees
- `lon: float` - Longitude in degrees
- `elevation: float` - Elevation in meters
- `temperature: float` - Temperature in Celsius
- `sea_level_temp: Optional[float]` - Temperature adjusted to sea level (populated during processing)

#### 3. `temperature_interpolation.py`
Core temperature-specific interpolation functions and orchestration.

**Key Functions:**
- `fetch_station_temperatures()`: Retrieves temperature data from WF1
- `adjust_temperature_to_sea_level()`: Normalizes station temps to sea level using lapse rate
- `adjust_temperature_to_elevation()`: Adjusts temps to terrain elevation using lapse rate
- `interpolate_temperature_to_raster()`: Main orchestration function
  - Uses `idw_interpolation()` from shared module
  - Employs `WPSDataset` for raster I/O
  - Combines elevation adjustment with spatial interpolation
- `upload_raster_to_s3()`: Uploads processed raster to object storage

**Domain-Specific Constants:**
- `DRY_ADIABATIC_LAPSE_RATE = 0.0098`: Temperature change per meter (9.8°C/km)

**Data Models:**
- Uses `StationTemperature` from `wps_shared.schemas.sfms`: Pydantic model for station data

**Raster Handling:**
- Uses `WPSDataset` for resource management and GDAL operations
- `WPSDataset.from_array()`: Creates output raster from NumPy array
- `export_to_geotiff()`: Exports with LZW compression

#### 4. `temperature_interpolation_processor.py`
High-level processor for orchestrating the workflow.

**Key Class:**
- `TemperatureInterpolationProcessor`: Manages the full interpolation pipeline
  - Fetches station metadata
  - Uses `get_auth_header` from `wfwx_api` for WF1 authentication
  - Coordinates data retrieval from WF1
  - Executes interpolation
  - Uses `RasterKeyAddresser.get_interpolated_key(datetime, WeatherParameter.TEMP)` for S3 path generation
  - Uploads results to S3 using `S3Client`

#### 5. `jobs/temperature_interpolation.py`
Job runner for executing interpolation as a batch process.

**Usage:**
```bash
# Run for current date
python -m app.jobs.temperature_interpolation

# Run for specific date
python -m app.jobs.temperature_interpolation "2024-01-15"
```

**S3 Integration:**
- Uses `S3Client` async context manager for efficient connection handling
- Follows the same pattern as other SFMS jobs (e.g., `sfms_calculations.py`)

### Storage Structure

Interpolated weather parameter rasters are stored in S3 with hierarchical date-based paths:

```
sfms/interpolated/{param}/YYYY/MM/DD/{param}_YYYYMMDD.tif
```

**Examples:**
```
sfms/interpolated/temp/2024/01/15/temp_20240115.tif
sfms/interpolated/rh/2024/01/15/rh_20240115.tif
sfms/interpolated/wind_speed/2024/01/15/wind_speed_20240115.tif
```

This structure:
- Allows efficient date-based browsing
- Supports multiple weather parameters using the same pattern
- Follows the pattern specified in the acceptance criteria
- Includes ISO date in filename for downloaded files
- Uses short parameter names matching `WeatherParameter` enum values (temp, rh, wind_speed)

### Raster Properties

**Output Format:**
- Format: GeoTIFF
- Data Type: Float32
- Compression: LZW
- Tiled: Yes
- NoData Value: -9999.0

**Spatial Reference:**
- Matches reference raster (typically fuel raster)
- BC Albers projection (EPSG:3005)
- Grid aligned with SFMS raster products

## Dependencies

### Data Inputs

1. **Weather Stations** (from WF1 API)
   - Station code, name, location (lat/lon)
   - Elevation (meters)
   - Temperature observations (°C)

2. **DEM** (Digital Elevation Model)
   - Source: S3 object storage
   - Path: `dem/mosaics/{DEM_NAME}`
   - Configuration: `config.get('DEM_NAME')`

3. **Reference Raster**
   - Defines output grid extent, resolution, and projection
   - Typically uses fuel raster: `sfms/static/{YEAR}/fbp{YEAR}_v{VERSION}.tif`

### Python Libraries

- `numpy`: Array operations and interpolation calculations
- `gdal/osr`: Low-level raster I/O and coordinate transformations
- `WPSDataset`: High-level GDAL wrapper for resource management
- `aiohttp`: Async HTTP requests to WF1 API
- `aiobotocore`: S3 object storage operations via `S3Client`
- `pydantic`: Data validation with `StationTemperature` model

## Testing

### Unit Tests

#### Spatial Interpolation Tests
Comprehensive test suite for the shared module in `wps_shared/tests/geospatial/test_spatial_interpolation.py`:

**Coverage (20 tests):**
- Module constants (IDW_POWER, SEARCH_RADIUS)
- Haversine distance calculation (same point, known distances, equator tests)
- IDW interpolation (exact matches, weighted averages, edge cases)
- None value filtering
- Search radius limits
- Custom power parameters
- Edge cases (negative values, large values, zero distance threshold)

**Run Tests:**
```bash
python -m pytest packages/wps-shared/src/wps_shared/tests/geospatial/test_spatial_interpolation.py -v
```

#### Temperature Interpolation Tests
Domain-specific test suite in `app/tests/sfms/test_temperature_interpolation.py`:

**Coverage (17 tests):**
- StationTemperature Pydantic model initialization
- Elevation adjustment (to/from sea level)
- Round-trip elevation adjustment validation
- Dry adiabatic lapse rate constant
- S3 key generation with hierarchical paths
- Full workflow integration with multiple stations

**Run Tests:**
```bash
python -m pytest packages/wps-api/src/app/tests/sfms/test_temperature_interpolation.py -v
```

**Total Test Coverage:** 37 tests (20 shared + 17 domain-specific)

### Integration Testing

To test with actual data:

1. **Set up environment:**
   ```bash
   export WFWX_BASE_URL="<WF1_API_URL>"
   export WFWX_USER="<username>"
   export WFWX_SECRET="<password>"
   export OBJECT_STORE_BUCKET="<bucket_name>"
   export DEM_NAME="<dem_filename.tif>"
   ```

2. **Run for a specific date:**
   ```bash
   python -m app.jobs.temperature_interpolation "2024-01-15"
   ```

3. **Verify output:**
   - Check S3 for raster: `sfms/interpolated/temp/2024/01/15/temp_20240115.tif`
   - Validate with QGIS or GDAL tools
   - Compare against existing SFMS temperature products

## Comparison with Current SFMS Output

### Verification Steps

As per acceptance criteria: "Verify Daily SFMS data according to our outputs"

1. **Visual Comparison:**
   - Load interpolated raster in QGIS
   - Load corresponding SFMS temperature product
   - Compare spatial patterns and values

2. **Statistical Comparison:**
   - Calculate raster statistics (min, max, mean, stddev)
   - Compare value ranges
   - Check for spatial correlation

3. **Station Cross-Validation:**
   - Extract interpolated values at station locations
   - Compare to original station observations
   - Calculate RMSE, MAE, and bias

## Configuration

### Environment Variables

- `WFWX_BASE_URL`: WF1 API base URL
- `WFWX_USER`: WF1 API username
- `WFWX_SECRET`: WF1 API password
- `OBJECT_STORE_BUCKET`: S3 bucket name
- `DEM_NAME`: DEM filename in S3
- `REDIS_USE`: Enable/disable Redis caching ("True"/"False")

### Adjustable Parameters

In `temperature_interpolation.py`:

```python
# Dry adiabatic lapse rate (°C per meter)
DRY_ADIABATIC_LAPSE_RATE = 0.0098

# IDW power parameter
IDW_POWER = 2.0

# Search radius (meters)
SEARCH_RADIUS = 200000  # 200 km
```

## Future Enhancements

### Using the Shared Spatial Interpolation Module

The `wps_shared.geospatial.spatial_interpolation` module is designed for reuse. Here's how to use it for other weather parameters:

#### Example: Dew Point Temperature Interpolation
```python
from wps_shared.geospatial.spatial_interpolation import idw_interpolation

# Fetch dew point observations
dew_point_lats = [s.lat for s in stations]
dew_point_lons = [s.lon for s in stations]
dew_point_values = [s.dew_point for s in stations if s.dew_point is not None]

# Interpolate (dew point also requires elevation adjustment like temperature)
interpolated_dew_point = idw_interpolation(
    target_lat, target_lon,
    dew_point_lats, dew_point_lons, dew_point_values
)
```

#### Example: Wind Speed Interpolation
```python
# Wind speed doesn't need elevation adjustment
wind_speed_lats = [s.lat for s in stations]
wind_speed_lons = [s.lon for s in stations]
wind_speed_values = [s.wind_speed for s in stations if s.wind_speed is not None]

# Interpolate with custom parameters
interpolated_wind = idw_interpolation(
    target_lat, target_lon,
    wind_speed_lats, wind_speed_lons, wind_speed_values,
    power=2.0,
    search_radius=150000  # 150km for wind
)
```

#### Example: Precipitation Interpolation
```python
# Precipitation may benefit from different power parameter
precip_lats = [s.lat for s in stations]
precip_lons = [s.lon for s in stations]
precip_values = [s.precipitation for s in stations if s.precipitation is not None]

interpolated_precip = idw_interpolation(
    target_lat, target_lon,
    precip_lats, precip_lons, precip_values,
    power=3.0  # Higher power for more localized influence
)
```

### Potential Improvements

1. **Alternative Interpolation Methods:**
   - Thin Plate Spline (mentioned in #4962)
   - Kriging with elevation as covariate
   - Machine learning-based spatial interpolation

2. **Performance Optimizations:**
   - Parallel processing of raster chunks
   - Spatial indexing for station lookup
   - Pre-compute distance matrices

3. **Quality Control:**
   - Automated outlier detection for station data
   - Cross-validation statistics
   - Comparison metrics against SFMS products

4. **Extended Variables:**
   - Dew point temperature interpolation (also requires elevation adjustment)
   - Relative humidity (calculated from interpolated temp and dew point)
   - Wind components (U/V) with IDW

## References

- Issue [#4995](https://github.com/bcgov/wps/issues/4995): SFMS Insights: Temperature Interpolation
- Issue [#4962](https://github.com/bcgov/wps/issues/4962): SFMS: Interpolation of weather parameters from station actuals
- Dry Adiabatic Lapse Rate: Standard atmospheric physics (9.8°C/km)
- IDW Interpolation: Shepard, D. (1968). "A two-dimensional interpolation function for irregularly-spaced data"

## Questions and Answers

### Q: Do we use all stations or just Prep Stations?
**A:** Use **all stations** that have valid temperature and elevation values (as per acceptance criteria).

### Q: Do we always use the dry adiabatic lapse rate?
**A:** Yes, the dry adiabatic lapse rate (9.8°C/km or 0.0098°C/m) is used for temperature adjustment. This is standard for free-air temperature adjustment in meteorology.

### Q: What if a station is missing elevation data?
**A:** Stations without elevation data are excluded from the interpolation. The code filters to only stations with non-null elevation values.

### Q: How are forecast vs. actual observations handled?
**A:** Only ACTUAL observations are used. Forecasts are filtered out during data fetching.

## Maintainers

- See [CODEOWNERS](../../CODEOWNERS) for responsible teams
- Related to SFMS Insights and Wildfire Predictive Services

## License

See project LICENSE file.
