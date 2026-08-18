# SFMS Fire Behaviour Prediction TODO

This document tracks the inputs and policy decisions needed to move SFMS from its standalone
Surface Fuel Consumption (SFC) calculation to a shared Fire Behaviour Prediction (FBP)
calculation. The intended primary outputs are SFC, Total Fuel Consumption, Rate of Spread, Crown
Fraction Burned, and Head Fire Intensity.

SFC should continue using `vectorized_surface_fuel_consumption` until the inputs below are ready.
Once another primary output is added, the SFC-only processor should be replaced by a multi-output
FBP processor that calls `vectorized_primary_fire_behaviour_prediction` once and publishes the
required fields from its result.

## Input TODOs

- [ ] Bring the existing legacy SFMS ground-slope and aspect rasters into the new pipeline,
  following the same approach used for the legacy DEM.
  - Ground slope (`gs`) must be expressed as percent slope, not degrees.
  - Aspect is the direction the slope faces. Convert it to radians before calling CFFDRS.
  - Define nodata handling and the aspect value used for flat pixels.
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
- [ ] Integrate the daily Foliar Moisture Content (FMC) raster.
  - Treat valid daily FMC values as authoritative rather than asking CFFDRS to derive them.
  - Require FMC to be finite and greater than `0` and at most `120` on pixels being calculated.
  - Exclude missing or invalid FMC pixels with the common valid-pixel mask. Passing them into
    CFFDRS would activate its location-and-date fallback and unintentionally fill missing data.
- [ ] Decide the Initial Spread Index policy.
  - The existing daily ISI raster is based on FFMC and interpolated wind without terrain effects.
  - Passing the existing positive ISI makes CFFDRS use it for the final ROS calculation.
  - Passing `isi=0` makes CFFDRS calculate ISI from FFMC and the slope-adjusted effective wind.
- [ ] Define the seasonal fuel-type policy.
  - Set the green-up/standing-period dates used to choose M1/M2, M3/M4, and O1A/O1B.
  - Resolve D1/D2 handling: the SFMS seasonal mapping includes D2, but the installed `cffdrs`
    package does not support D2 as an FBP fuel type.

## Inputs Already Available or Derivable

| CFFDRS argument | Source or policy | Units and notes |
| --- | --- | --- |
| `fuel_type_code` | Year-specific fuel raster and SFMS classification mapping | Apply seasonal variants before converting to CFFDRS codes. |
| `ffmc` | Same-day FFMC raster | Existing FWI output. |
| `bui` | Same-day BUI raster | Existing FWI output. |
| `ws` | Same-day interpolated wind-speed raster | km/h. |
| `wd_rad` | Same-day interpolated wind-direction raster | Existing raster is meteorological degrees; convert to radians. |
| `gs` | Existing legacy SFMS slope raster | Percent slope; migrate and address it in the new pipeline. |
| `aspect_rad` | Existing legacy SFMS aspect raster | Downslope aspect converted to radians; migrate and address it in the new pipeline. |
| `pc` | Percent-conifer raster paired with the fuel-grid year | Required and validated on M1/M2 pixels. Use zero elsewhere. |
| `pdf` | Conditional percent-dead-balsam-fir source | First confirm M3/M4 occurs in the selected fuel grid. If it does, require and validate PDF on those pixels; use zero elsewhere. |
| `cc` | Grass-curing source to be determined | Required and validated on O1A/O1B pixels. Use zero elsewhere. |
| `gfl` | Fixed value | `0.35 kg/m²`, matching the existing SFC calculation. |
| `cbh` | Default policy to confirm | Candidate value: `0`, which selects the CFFDRS fuel-type default; confirm before implementation. |
| `cfl` | Default policy to confirm | Candidate value: `0`, which selects the CFFDRS fuel-type default; confirm before implementation. |
| `fmc` | Daily FMC raster | Require a finite value in `(0, 120]`; missing or invalid pixels become output nodata. |
| `isi` | Policy to be decided | Pass a positive value to use the existing daily ISI, or `0` to have CFFDRS derive it from FFMC and effective wind. |
| `lat` | Unused-input policy to confirm | Candidate placeholder: `0`; valid FMC prevents CFFDRS from reading it. Confirm before implementation. |
| `lon` | Unused-input policy to confirm | Candidate placeholder: `0`; valid FMC prevents CFFDRS from reading it. Confirm before implementation. |
| `elv` | Unused-input policy to confirm | Candidate placeholder: `0`; valid FMC prevents CFFDRS from reading it. Confirm before implementation. |
| `dj` | Unused-input policy to confirm | Candidate placeholder: `0`; valid FMC prevents CFFDRS from reading it. Confirm before implementation. |
| `d0` | Unused-input policy to confirm | Candidate placeholder: `0`; valid FMC prevents CFFDRS from reading it. Confirm before implementation. |
| `sd` | Default policy to confirm | Candidate value: `0`, which makes C6 use its fuel-type CBH default; confirm before implementation. |
| `sh` | Default policy to confirm | Candidate value: `0`, which makes C6 use its fuel-type CBH default; confirm before implementation. |
| `hr` | Primary-control policy to confirm | Candidate value: `0`; elapsed time is not used by the planned primary products. Confirm before implementation. |
| `theta_rad` | Primary-control policy to confirm | Candidate value: `0`; directional secondary outputs are not planned. Confirm before implementation. |
| `accel` | Primary-control policy to confirm | Candidate value: `0`, which produces equilibrium ROS; confirm before implementation. |
| `buieff` | Fixed calculation control | Pass `1` to apply the BUI effect. |

## Pipeline Requirements

- [ ] Define a shared `FBPInputs` raster contract once the unresolved data sources are known.
- [ ] Require all input rasters to match the selected fuel grid's extent, resolution, projection,
  and geotransform.
- [ ] Validate fuel-specific inputs only where they are meaningful: PC on M1/M2, PDF on M3/M4,
  and grass curing on O1A/O1B.
- [ ] Apply the BC mask as the final mask for every primary output. Publish nodata outside BC and
  where required inputs are missing or invalid; publish `0` for recognized non-combustible fuel
  pixels inside BC.
- [ ] Replace `SurfaceFuelConsumptionProcessor` rather than running both the standalone SFC and
  shared primary FBP calculations.
- [ ] During that transition, verify the shared primary calculation's SFC output matches the
  standalone SFC calculation for every supported fuel type.

## Deferred Outputs

- Thirty-minute fire size requires secondary fire-geometry outputs and is intentionally deferred.
- Wildfire Ignition Probability is a separate downstream model, not a CFFDRS primary or secondary
  output.
