import { TextField, Autocomplete } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { BasicWFWXStation, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { isEqual, isNull } from 'lodash'
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
  handleEditStation: (planningAreaId: number, rowId: number, row: StationAdminRow) => void
}

export const AdminStationDropdown = ({
  adminRow,
  planningAreaId,
  stationOptions,
  handleEditStation
}: AdminStationDropdownProps) => {
  const classes = useStyles()
  return (
    <Autocomplete
      className={classes.autocomplete}
      data-testid={'admin-select-station'}
      disableClearable
      autoSelect
      value={adminRow.station}
      options={stationOptions}
      getOptionLabel={option => option?.name}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      renderInput={params => <TextField {...params} label="Select Station" variant="outlined" />}
      onChange={(_, value) => {
        if (!isNull(value)) {
          handleEditStation(planningAreaId, adminRow.rowId, {
            ...adminRow,
            station: { ...value }
          })
        }
      }}
    />
  )
}
