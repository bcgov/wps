import { TextField, Autocomplete } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FuelType } from 'api/hfiCalculatorAPI'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { isEqual } from 'lodash'
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
}

export const AdminFuelTypesDropdown = ({ adminRow, fuelTypes, disabled }: AdminFuelTypesDropdownProps) => {
  const classes = useStyles()
  return (
    <Autocomplete
      className={classes.autocomplete}
      data-testid={'admin-fuel-type'}
      disableClearable
      disabled={disabled}
      value={adminRow.fuelType}
      options={fuelTypes}
      getOptionLabel={option => option?.abbrev}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      renderInput={params => <TextField {...params} label="Fuel Type" variant="outlined" />}
    />
  )
}
