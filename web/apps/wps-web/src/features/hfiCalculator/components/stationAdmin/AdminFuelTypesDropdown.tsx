import { TextField, Autocomplete } from '@mui/material'
import { styled } from '@mui/material/styles'
import { FuelType } from 'api/hfiCalculatorAPI'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import { isEqual, isNull, isUndefined } from 'lodash'
import React from 'react'

const PREFIX = 'AdminFuelTypesDropdown'

const AdminFuelTypeTextField = styled(TextField, {
  name: `${PREFIX}-adminFuelTypeTextField`
})({
  minWidth: 300
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
      data-testid={testId}
      disableClearable
      disabled={disabled}
      value={adminRow.fuelType}
      options={fuelTypes}
      getOptionLabel={option => option?.abbrev}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      renderInput={params => (
        <AdminFuelTypeTextField
          {...params}
          label="Fuel Type"
          variant="outlined"
          error={isUndefined(adminRow.fuelType)}
        />
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
