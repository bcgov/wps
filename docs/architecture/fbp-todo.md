# SFMS Fire Behaviour Prediction TODO

This document tracks the inputs and policy decisions for the shared Fire Behaviour Prediction
(FBP) calculation. One call to `vectorized_primary_fire_behaviour_prediction` currently publishes
Surface Fuel Consumption (SFC), Rate of Spread (ROS), Head Fire Intensity (HFI), Total Fuel
Consumption (TFC), and Crown Fraction Burned (CFB).

## Input TODOs

- [x] Convert interpolated wind direction before calling the vectorized CFFDRS calculation.
  - The raster stores meteorological direction in degrees, while `wd_rad` expects radians.
  - Preserve nodata in the common valid-pixel mask, normalize valid values modulo 360, and convert
    them with `np.radians` at the calculation boundary.
- [x] Bring the existing legacy SFMS ground-slope and aspect rasters into the new pipeline,
      following the same approach used for the legacy DEM.
  - `bc_slope.tif` is a 778 by 683, 2 km Float32 raster in percent slope. Its valid values span
    approximately `-14%` to `309%`; clamp them to `[0, 70]` at the calculation boundary, matching
    the maximum slope used by the legacy SFMS/CFFDRS slope adjustment.
  - `bc_aspect.tif` has the same grid and is a Float32 downslope-aspect raster in degrees. Its valid
    values span approximately `-56` to `408`; normalize modulo 360 and convert to radians at the
    calculation boundary.
  - Preserve terrain nodata in the common valid-pixel mask. Use aspect `0` where the clamped slope
    is zero because aspect has no effect on flat pixels.
  - Do not regenerate these rasters from the 2 km `bc_elevation.tif`. Test derivatives from that
    coarse DEM were substantially flatter and poorly matched the legacy terrain rasters, which
    likely retain information derived from a finer elevation source.
- [ ] Confirm whether production fuel grids contain the M3/M4 classification before sourcing
      percent dead balsam fir (`pdf`).
  - The temporary classification mapping reserves value `13` for M3/M4, but the temporary 2025
    raster currently contains no value `13` pixels.
  - If a selected fuel grid contains M3/M4 pixels, identify an appropriate PDF source and decide
    whether it must be paired with the fuel-grid year.
  - If M3/M4 is absent, use zero for PDF and defer acquiring a dedicated raster.
  - If PDF is required, missing or out-of-range values on M3/M4 pixels should prevent calculation
    rather than silently use a generic percentage.
- [ ] Identify, retain, and align an initial percent-grass-curing (`cc`) raster source.
  - It is only meaningful for O1A/O1B pixels.
  - The initial source and update cadence still need to be determined.
  - Define staleness and fallback rules once the source is selected.
- [x] Generate one shared Foliar Moisture Content (FMC) raster per calendar date from the
      SFMSNG elevation, latitude, and longitude grids.
  - Actual jobs ensure their target date exists; forecast jobs ensure their three processed
    dates exist. Existing GeoTIFF and COG pairs are reused.
  - FMC rasters are stored under `sfms_ng/static/fmc/YYYY/MM/DD/`
- [x] Integrate the daily FMC raster into the shared primary FBP calculation.
  - Treat valid daily FMC values as authoritative rather than asking CFFDRS to derive them.
  - Require FMC to be finite and greater than `0` and at most `120` on pixels being calculated.
  - Exclude missing or invalid FMC pixels with the common valid-pixel mask. Passing them into
    CFFDRS would activate its location-and-date fallback and unintentionally fill missing data.
- [x] Have the primary FBP calculation derive its Initial Spread Index.
  - The existing daily ISI raster is based on FFMC and interpolated wind without terrain effects.
  - Pass `isi=0` so CFFDRS calculates ISI from FFMC and the slope-adjusted effective wind.
  - Continue producing the daily FWI ISI raster as an FWI output, but do not use it as a primary
    FBP input.
- [ ] Define the seasonal fuel-type policy.
  - Set the green-up/standing-period dates used to choose M1/M2, M3/M4, and O1A/O1B.
  - Resolve D1/D2 handling: the SFMS seasonal mapping includes D2, but the installed `cffdrs`
    package does not support D2 as an FBP fuel type.

## Inputs Already Available or Derivable

| CFFDRS argument  | Source or policy                                          | Units and notes                                                                                                                 |
| ---------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `fuel_type_code` | Year-specific fuel raster and SFMS classification mapping | Apply seasonal variants before converting to CFFDRS codes.                                                                      |
| `ffmc`           | Same-day FFMC raster                                      | Existing FWI output.                                                                                                            |
| `bui`            | Same-day BUI raster                                       | Existing FWI output.                                                                                                            |
| `ws`             | Same-day interpolated wind-speed raster                   | km/h.                                                                                                                           |
| `wd_rad`         | Same-day interpolated wind-direction raster               | Meteorological degrees; normalize modulo 360 and convert valid values with `np.radians`.                                        |
| `gs`             | Existing legacy SFMS slope raster                         | Percent slope; clamp valid values to `[0, 70]`.                                                                                 |
| `aspect_rad`     | Existing legacy SFMS aspect raster                        | Downslope aspect in degrees; normalize modulo 360, convert to radians, and use `0` on flat pixels.                              |
| `pc`             | Percent-conifer raster paired with the fuel-grid year     | Required and validated on M1/M2 pixels. Use zero elsewhere.                                                                     |
| `pdf`            | Conditional percent-dead-balsam-fir source                | First confirm M3/M4 occurs in the selected fuel grid. If it does, require and validate PDF on those pixels; use zero elsewhere. |
| `cc`             | Grass-curing source to be determined                      | Required and validated on O1A/O1B pixels. Use zero elsewhere.                                                                   |
| `gfl`            | Fixed value                                               | `0.35 kg/m²`, matching the existing SFC calculation.                                                                            |
| `cbh`            | Default policy to confirm                                 | Candidate value: `0`, which selects the CFFDRS fuel-type default; confirm before implementation.                                |
| `cfl`            | Default policy to confirm                                 | Candidate value: `0`, which selects the CFFDRS fuel-type default; confirm before implementation.                                |
| `fmc`            | Daily FMC raster                                          | Require a finite value in `(0, 120]`; missing or invalid pixels become output nodata.                                           |
| `isi`            | Fixed calculation control                                 | Pass `0` so CFFDRS derives it from FFMC and the slope-adjusted effective wind.                                                  |
| `lat`            | Fixed placeholder                                         | Pass `0`; valid FMC prevents CFFDRS from reading it.                                                                            |
| `lon`            | Fixed placeholder                                         | Pass `0`; valid FMC prevents CFFDRS from reading it.                                                                            |
| `elv`            | Fixed placeholder                                         | Pass `0`; valid FMC prevents CFFDRS from reading it.                                                                            |
| `dj`             | Fixed placeholder                                         | Pass `0`; valid FMC prevents CFFDRS from reading it.                                                                            |
| `d0`             | Fixed placeholder                                         | Pass `0`; valid FMC prevents CFFDRS from reading it.                                                                            |
| `sd`             | Default policy to confirm                                 | Candidate value: `0`, which makes C6 use its fuel-type CBH default; confirm before implementation.                              |
| `sh`             | Default policy to confirm                                 | Candidate value: `0`, which makes C6 use its fuel-type CBH default; confirm before implementation.                              |
| `hr`             | Primary-control policy to confirm                         | Candidate value: `0`; elapsed time is not used by the planned primary products. Confirm before implementation.                  |
| `theta_rad`      | Primary-control policy to confirm                         | Candidate value: `0`; directional secondary outputs are not planned. Confirm before implementation.                             |
| `accel`          | Primary-control policy to confirm                         | Candidate value: `0`, which produces equilibrium ROS; confirm before implementation.                                            |
| `buieff`         | Fixed calculation control                                 | Pass `1` to apply the BUI effect.                                                                                               |

## Pipeline Requirements

- [x] Define a shared primary-FBP raster contract for the current SFC, ROS, HFI, TFC, and CFB
      outputs.
- [x] Require all input rasters to match the selected fuel grid's extent, resolution, projection,
      and geotransform.
- [ ] Validate fuel-specific inputs only where they are meaningful: PC on M1/M2, PDF on M3/M4,
      and grass curing on O1A/O1B.
- [x] Apply the BC mask as the final mask for every primary output. Publish nodata outside BC and
      where required inputs are missing or invalid; publish `0` for recognized non-combustible fuel
      pixels inside BC.
- [x] Replace `SurfaceFuelConsumptionProcessor` rather than running both the standalone SFC and
      shared primary FBP calculations.
- [x] During that transition, verify the shared primary calculation's SFC output matches the
      standalone SFC calculation for every supported fuel type.

## Deferred Outputs

- Thirty-minute fire size requires secondary fire-geometry outputs and is intentionally deferred.
- Wildfire Ignition Probability is a separate downstream model, not a CFFDRS primary or secondary
  output.
