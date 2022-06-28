import { TextField, Autocomplete } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { BasicWFWXStation, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { isEqual } from 'lodash'
import React from 'react'

const useStyles = makeStyles({
  autocomplete: {
    minWidth: 300
  }
})

export interface AdminStationDropdownProps {
  testId?: string
  adminRow: StationAdminRow
  planningAreaId: number
  stationOptions: BasicWFWXStation[]
  disabled: boolean
}

export const AdminStationDropdown = ({ adminRow, stationOptions, disabled }: AdminStationDropdownProps) => {
  const classes = useStyles()
  return (
    <Autocomplete
      className={classes.autocomplete}
      data-testid={'admin-select-station'}
      disableClearable
      disabled={disabled}
      value={adminRow.station}
      options={stationOptions}
      getOptionLabel={option => option?.name}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      renderInput={params => <TextField {...params} label="Station" variant="outlined" />}
    />
  )
}
