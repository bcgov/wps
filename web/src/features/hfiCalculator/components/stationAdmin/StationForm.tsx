import React from 'react'
import { Autocomplete, TextField, Grid, IconButton } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { AddStationOptions } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { isEqual } from 'lodash'
import { StationAdminRow } from 'features/hfiCalculator/stationAdmin/admin'
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined'

export interface StationFormProps {
  testId?: string
  rowId: number
  adminRow: StationAdminRow
  planningAreaId: number
  addStationOptions?: AddStationOptions
}

const useStyles = makeStyles({
  autocomplete: {
    minWidth: 300
  }
})

export const StationForm = ({ adminRow, addStationOptions, planningAreaId, rowId }: StationFormProps): JSX.Element => {
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
              value={{ name: adminRow.station.name, code: adminRow.station.code }}
              options={addStationOptions ? addStationOptions.stations : []}
              getOptionLabel={option => option?.name}
              isOptionEqualToValue={(option, value) => isEqual(option, value)}
              renderInput={params => <TextField {...params} label="Select Station" variant="outlined" />}
              onChange={(_, value) => {
                /** TODO */
                console.log(value, planningAreaId, rowId)
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
                /** TODO */
                console.log(value, planningAreaId, rowId)
              }}
            />
          </Grid>
          <Grid item>
            <IconButton size="large">
              <DeleteOutlinedIcon />
            </IconButton>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  )
}

export default React.memo(StationForm)
