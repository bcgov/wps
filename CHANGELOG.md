## 2022-04-19 HFI Calc - Kelowna Station Additions [#1849](https://github.com/bcgov/wps/issues/1849)

### Features

- **hfi calculator:** Added West Kelowna (1277) station with fuel type C7 to Penticton planning area as 2nd station in list. Added Station Bay 2 (1359) station with fuel type C5 to Vernon planning area as 3rd station in list

## 2022-04-14 HFI Calc - Bug Fix - PDF Download

### Bug

- Fixed: PDF request was returning PDF for start date only, and would not honour station selected & fire starts for prep periods in excess of one day.

## 2022-04-13 HFI Calc - Refactor Request & Response Structure [#1555](https://github.com/bcgov/wps/issues/1555)

### Refactor

- **hfi calculator** Changed HFI request and result structure, remove selected_station_code_ids and made request/response structure more strict.

## 2022-04-12 HFI Calc : Success Snackbar [#1634](https://github.com/bcgov/wps/issues/1634)

### Features

- **hfi calculator:** Add a success snackbar that shows when user has successfully made a change to prep.

## 2022-04-11 HFI Calc : Prep Period [#1634](https://github.com/bcgov/wps/issues/1634)

### Features

- **hfi calculator:** Load the most recently saved prep record that overlaps with the current date. (Previous behaviour was to load the most recently modified prep record.)
- **hfi calculator:** Changing the prep period date does not result in a write to the database. Users can change thus change dates without affecting other users. (Previous behaviour was to create/update a prep record when changing the date.)
- **hfi calculator:** When a fire starts are changed or weather stations are toggled, a prep period record is created in the database.
- **hfi calculator:** Changing the prep period end date results in losing fire starts & weather station toggles. (Previous behaviour would retain fire starts & weather station toggles if the start date was unchanged.)
- **hfi calculator:** Changed warning message from "Any changes made to dates, fire starts or selected stations ..." to "Any changes made to fire starts or selected stations..."
