## 2022-05-11 HFI Calc [#1869](https://github.com/bcgov/wps/issues/1869),[#1871](https://github.com/bcgov/wps/issues/1871),[#1869](https://github.com/bcgov/wps/issues/1869)

### Features

- **hfi calculator:** Introduce role permission for editing HFI prep fire starts, fuel types and station selection.

## 2022-05-10 FBA Calculator

### Bug

## 2022-05-10 FBA Calculator - Recalculated FWI was not being propogated back to front end on wind speed override.

### Bug

- Fixed [#1981](https://github.com/bcgov/wps/issues/1981): C7B fuel type lookup looking was wrong, causing C7 calculations.

## 2022-04-28 Fire Behaviour Calc - 422 bug caused by missing station

## 2022-04-28 HFI Calc - Refactor + Grass Cure Display Bug

### Bug

- Fixed: Warning that grass cure is not set was using default fuel type, instead of selected fuel type.

### Refactor

- Refactoring code.

## 2022-04-27 HFI Calc - Set fuel type

### Features

- **hfi calculator [#1555](https://github.com/bcgov/wps/issues/1555):** Change fuel type for weather stations in HFI calculation.

## 2022-04-26 HFI Calc - Migrate Material UI from v4 to v5, Part1 [#1896](https://app.zenhub.com/workspaces/wildfire-predictive-services-5e321393e038fba5bbe203b8/issues/bcgov/wps/1896)

### Refactor

- **all products** Added the new libraries, updated component imports and ran the codemod while keeping the existing CSS in JSS libraries in place. Eventually (part 2) we will remove the CSS in JS build library in favor of the direction MaterialUI is going with the emotion CSS engine.

## 2022-04-21 HFI Calc

### Bug

- Fixed [#1904](https://github.com/bcgov/wps/issues/1904): Initial load of the page would not render loading spinner

## 2022-04-19 HFI Calc

### Features

- **hfi calculator [#1849](https://github.com/bcgov/wps/issues/1849):** Added West Kelowna (1277) station with fuel type C7 to Penticton planning area as 2nd station in list. Added Station Bay 2 (1359) station with fuel type C5 to Vernon planning area as 3rd station in list

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
