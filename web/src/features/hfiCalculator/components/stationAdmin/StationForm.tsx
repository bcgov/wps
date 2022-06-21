import React from 'react'
import { Autocomplete, TextField, Grid, IconButton } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { AdminHandlers } from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import { isEqual, isUndefined } from 'lodash'
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined'

export interface StationFormProps {
  testId?: string
  adminRow: StationAdminRow
  planningAreaId: number
  addStationOptions?: AddStationOptions
  adminHandlers: AdminHandlers
}

const useStyles = makeStyles({
  autocomplete: {
    minWidth: 300
  }
})

export const StationForm = ({
  adminRow,
  addStationOptions,
  planningAreaId,
  adminHandlers
}: StationFormProps): JSX.Element => {
  const classes = useStyles()

  return (
    <Grid container spacing={1} sx={{ pt: 1 }}>
      <Grid item>
        <Grid container direction="row" spacing={1}>
          <Grid item>
            <Autocomplete
              className={classes.autocomplete}
              data-testid={'select-station'}
              disableClearable
              value={adminRow.station}
              options={addStationOptions ? addStationOptions.stations : []}
              getOptionLabel={option => option?.name}
              isOptionEqualToValue={(option, value) => isEqual(option, value)}
              renderInput={params => <TextField {...params} label="Select Station" variant="outlined" />}
              onChange={(_, value) => {
                if (!isUndefined(adminRow.station)) {
                  adminHandlers.handleEditStation(planningAreaId, adminRow.rowId, {
                    ...adminRow,
                    station: { ...value }
                  })
                }
              }}
            />
          </Grid>
          <Grid item>
            <Autocomplete
              className={classes.autocomplete}
              data-testid={'select-fuel-type'}
              disableClearable
              value={adminRow.fuelType}
              options={addStationOptions ? addStationOptions.fuel_types : []}
              getOptionLabel={option => option?.abbrev}
              isOptionEqualToValue={(option, value) => isEqual(option, value)}
              renderInput={params => <TextField {...params} label="Select Fuel Type" variant="outlined" />}
              onChange={(_, value) => {
                if (!isUndefined(adminRow.fuelType)) {
                  adminHandlers.handleEditStation(planningAreaId, adminRow.rowId, {
                    ...adminRow,
                    fuelType: { ...value }
                  })
                }
              }}
            />
          </Grid>
          <Grid item>
            <IconButton
              color="primary"
              size="large"
              onClick={() => {
                if (!isUndefined(adminRow)) {
                  adminHandlers.handleRemoveStation(planningAreaId, adminRow.rowId)
                }
              }}
            >
              <DeleteOutlinedIcon />
            </IconButton>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  )
}

export default React.memo(StationForm)
