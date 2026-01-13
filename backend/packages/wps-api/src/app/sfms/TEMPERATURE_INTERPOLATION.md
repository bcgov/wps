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

#### 0. `wps_shared.schemas.sfms.StationTemperature`
Pydantic data model for station temperature data.

**Fields:**
- `code: int` - Station code
- `lat: float` - Latitude in degrees
- `lon: float` - Longitude in degrees
- `elevation: float` - Elevation in meters
- `temperature: float` - Temperature in Celsius
- `sea_level_temp: Optional[float]` - Temperature adjusted to sea level (populated during processing)

#### 1. `temperature_interpolation.py`
Core interpolation functions and utilities.

**Key Functions:**
- `fetch_station_temperatures()`: Retrieves temperature data from WF1
- `adjust_temperature_to_sea_level()`: Normalizes station temps to sea level
- `adjust_temperature_to_elevation()`: Adjusts temps to terrain elevation
- `haversine_distance()`: Calculates great circle distance between points
- `idw_interpolation()`: Performs IDW interpolation for a single point
- `interpolate_temperature_to_raster()`: Main orchestration function using `WPSDataset`
- `get_interpolated_temp_key()`: Generates S3 storage path

**Data Models:**
- Uses `StationTemperature` from `wps_shared.schemas.sfms`: Pydantic model for station data with temperature and location

**Raster Handling:**
- Uses `WPSDataset` for resource management and GDAL operations
- `WPSDataset.from_array()`: Creates output raster from NumPy array
- `export_to_geotiff()`: Exports with LZW compression

#### 2. `temperature_interpolation_processor.py`
High-level processor for orchestrating the workflow.

**Key Class:**
- `TemperatureInterpolationProcessor`: Manages the full interpolation pipeline
  - Fetches station metadata
  - Coordinates data retrieval from WF1
  - Executes interpolation
  - Uploads results to S3 using `S3Client`

#### 3. `jobs/temperature_interpolation.py`
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

Temperature rasters are stored in S3 with hierarchical date-based paths:

```
sfms/interpolated/temperature/YYYY/MM/DD/temperature_YYYYMMDD.tif
```

**Example:**
```
sfms/interpolated/temperature/2024/01/15/temperature_20240115.tif
```

This structure:
- Allows efficient date-based browsing
- Follows the pattern specified in the acceptance criteria
- Includes ISO date in filename for downloaded files

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

Comprehensive test suite in `app/tests/sfms/test_temperature_interpolation.py`:

**Test Coverage:**
- StationTemperature initialization
- Elevation adjustment (to/from sea level)
- Round-trip elevation adjustment
- Haversine distance calculation
- IDW interpolation edge cases
- S3 key generation
- Full workflow integration

**Run Tests:**
```bash
cd /Users/cbrady/projects/wps/backend
python -m pytest packages/wps-api/src/app/tests/sfms/test_temperature_interpolation.py -v
```

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
   - Check S3 for raster: `sfms/interpolated/temperature/2024/01/15/temperature_20240115.tif`
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
