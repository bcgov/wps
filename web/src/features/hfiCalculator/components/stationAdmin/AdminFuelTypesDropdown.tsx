import { TextField, Autocomplete } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FuelType } from 'api/hfiCalculatorAPI'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { isEqual, isNull, isUndefined } from 'lodash'
import React from 'react'

const useStyles = makeStyles({
  autocomplete: {
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
  const classes = useStyles()
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
      renderInput={params => <TextField {...params} label="Fuel Type" variant="outlined" />}
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
