# Storage assumptions

## Method

- Reviewed disk usage in postgres database and backup after running env-canada and noon-forecast cronjob.
- Reviewed current database backup files to establish compression ratio.

## Assumptions

- Optimization by a factor of 10 on env-canada job should be feasable.
- Compression ratio for backup will remain consistent.
- Forecast data has very little room for optimization.

Refer to storage_assumptions spreadsheet for further assumptions and details of calculations.

## Scenario 1 : current

Assuming no changes to the application and how it is run as of 2020 August 11.

- Storage: Run out of space in 28.5 years, sufficient storage available.
- Backup: Run out of space in 0.5 years. Require at least 11 GB, ideally 42 GB.

## Scenario 2 : projected

Assuming no changes in how data is stored, adding additional fields and adding the high resolution regional model.

- Storage: Run out of space in 0.8 years. Required 1.2TB.
- Backup: Run out of space in 0.0 years. Require at least 669GB, ideally 1.4TB.

## Scenario 3 - projected, with optimizations

Assuming adding additional fields but optimizing by rolling up values (e.g. storing percentiles, interpolated values and getting rid of raw data) would result in optimizing by a factor of 10.

- Storage: Run out of space in 8.1 years, sufficient storage available.
- Backup: Run out of space in 0.1 years. Require at least 68GB, ideally 149GB.
