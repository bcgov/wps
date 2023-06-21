import { TextField, Autocomplete } from '@mui/material'
import { styled } from '@mui/material/styles'
import { FuelType } from 'api/hfiCalculatorAPI'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import { isEqual, isNull, isUndefined } from 'lodash'
import React from 'react'

const PREFIX = 'AdminFuelTypesDropdown'

const classes = {
  autocomplete: `${PREFIX}-autocomplete`
}

const StyledTextField = styled(TextField)({
  [`& .${classes.autocomplete}`]: {
    minWidth: 300
  }
})

export interface AdminFuelTypesDropdownProps {
  testId?: string
  adminRow: StationAdminRow
  planningAreaId: number
  fuelTypes: Pick<FuelType, 'id' | 'abbrev'>[]
  disabled: boolean
  handleEditStation?: (planningAreaId: number, rowId: number, station: StationAdminRow) => void
}

export const AdminFuelTypesDropdown = ({
  testId,
  adminRow,
  fuelTypes,
  disabled,
  handleEditStation
}: AdminFuelTypesDropdownProps) => {
  return (
    <Autocomplete
      className={classes.autocomplete}
      data-testid={testId}
      disableClearable
      disabled={disabled}
      value={adminRow.fuelType}
      options={fuelTypes}
      getOptionLabel={option => option?.abbrev}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      renderInput={params => (
        <StyledTextField {...params} label="Fuel Type" variant="outlined" error={isUndefined(adminRow.fuelType)} />
      )}
      onChange={(_, value) => {
        if (!isNull(value) && !isUndefined(handleEditStation)) {
          handleEditStation(adminRow.planningAreaId, adminRow.rowId, {
            ...adminRow,
            fuelType: { ...value }
          })
        }
      }}
    />
  )
}
