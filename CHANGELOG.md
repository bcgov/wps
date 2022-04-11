## 2022-04-11 HFI Calc [#1634](https://github.com/bcgov/wps/issues/1634)

### Features

- **hfi calculator:** Load the most recently saved prep record that overlaps with the current date. (Previous behaviour was to load the most recently modified prep record.)

- **hfi calculator:** Changing the prep period date does not result in a write to the database. Users can change thus change dates without affecting other users. (Previous behaviour was to create/update a prep record when changing the date.)
- **hfi calculator:** When a fire starts are changed or weather stations are toggled, a prep period record is created in the database.
- **hfi calculator:** Changing the prep period end date results in losing fire starts & weather station toggles. (Previous behaviour would retain fire starts & weather station toggles if the start date was unchanged.)
- **hfi calculator:** Changed warning message from "Any changes made to dates, fire starts or selected stations ..." to "Any changes made to fire starts or selected stations..."
