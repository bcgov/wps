import React from 'react'
import { Autocomplete, TextField, Grid } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FuelType, WeatherStation } from 'api/hfiCalculatorAPI'
import { AddStationOptions } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { isEqual } from 'lodash'

export interface StationFormProps {
  testId?: string
  planningAreaId: number
  station: WeatherStation
  fuelType?: FuelType
  addStationOptions?: AddStationOptions
}

const useStyles = makeStyles({
  autocomplete: {
    minWidth: 300
  },
  tooltip: {
    maxHeight: '0.75em'
  },
  toolTipText: {
    fontSize: 14
  }
})

export const StationForm = ({
  station,
  addStationOptions,
  fuelType,
  planningAreaId
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
              value={{ name: station.station_props.name, code: station.code }}
              options={addStationOptions ? addStationOptions.stations : []}
              getOptionLabel={option => option?.name}
              isOptionEqualToValue={(option, value) => isEqual(option, value)}
              renderInput={params => <TextField {...params} label="Select Station" variant="outlined" />}
              onChange={(_, value) => {
                /** TODO */
                console.log(value, planningAreaId)
              }}
            />
          </Grid>
          <Grid item>
            <Autocomplete
              data-testid={'select-fuel-type'}
              className={classes.autocomplete}
              value={fuelType}
              options={addStationOptions ? addStationOptions.fuel_types : []}
              getOptionLabel={option => option?.abbrev}
              isOptionEqualToValue={(option, value) => isEqual(option, value)}
              renderInput={params => <TextField {...params} label="Select Fuel Type" variant="outlined" />}
              onChange={(_, value) => {
                /** TODO */
                console.log(value, planningAreaId)
              }}
            />
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  )
}

export default React.memo(StationForm)
