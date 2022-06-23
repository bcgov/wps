import { TextField, Autocomplete } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FuelType } from 'api/hfiCalculatorAPI'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { isEqual, isNull } from 'lodash'
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
  handleEditStation: (planningAreaId: number, rowId: number, row: StationAdminRow) => void
}

export const AdminFuelTypesDropdown = ({
  adminRow,
  planningAreaId,
  fuelTypes,
  handleEditStation
}: AdminFuelTypesDropdownProps) => {
  const classes = useStyles()
  return (
    <Autocomplete
      className={classes.autocomplete}
      data-testid={'admin-select-fuel-type'}
      disableClearable
      autoSelect
      value={adminRow.fuelType}
      options={fuelTypes}
      getOptionLabel={option => option?.abbrev}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      renderInput={params => <TextField {...params} label="Select Fuel Type" variant="outlined" />}
      onChange={(_, value) => {
        if (!isNull(adminRow.fuelType)) {
          handleEditStation(planningAreaId, adminRow.rowId, {
            ...adminRow,
            fuelType: { ...value }
          })
        }
      }}
    />
  )
}
