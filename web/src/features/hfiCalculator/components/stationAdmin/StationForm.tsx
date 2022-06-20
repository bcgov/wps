import React from 'react'
import { Autocomplete, TextField, Grid } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { WeatherStation } from 'api/hfiCalculatorAPI'
import { AddStationOptions } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { isEqual } from 'lodash'

export interface StationFormProps {
  testId?: string
  station: WeatherStation
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

export const StationForm = ({ station, addStationOptions }: StationFormProps): JSX.Element => {
  const classes = useStyles()

  //   const invalidNewStation = (station: AdminStation) => {
  //     const missingFields =
  //       isUndefined(station.planningArea) || isUndefined(station.station) || isUndefined(station.fuelType)
  //     setInvalid(missingFields && station.dirty)
  //   }

  //   const planningAreaError = (newStation.dirty && isUndefined(newStation.planningArea)) || !isNull(stationAddedError)

  //   const stationError = (newStation.dirty && isUndefined(newStation.station)) || !isNull(stationAddedError)

  //   const fuelTypeError = (newStation.dirty && isUndefined(newStation.fuelType)) || !isNull(stationAddedError)

  //   const toolTipText = <div className={classes.toolTipText}>Grass curing is set in WFWX</div>

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
                console.log(value)
              }}
            />
          </Grid>
          <Grid item>
            <Autocomplete
              data-testid={'select-fuel-type'}
              className={classes.autocomplete}
              options={addStationOptions ? addStationOptions.fuel_types : []}
              getOptionLabel={option => option?.abbrev}
              isOptionEqualToValue={(option, value) => isEqual(option, value)}
              renderInput={params => <TextField {...params} label="Select Fuel Type" variant="outlined" />}
              onChange={(_, value) => {
                /** TODO */
                console.log(value)
              }}
            />
          </Grid>
        </Grid>
      </Grid>
      {/* {invalid && (
          <Grid container direction="row" justifyContent="center" spacing={1} marginTop={5}>
            <Grid item>
              <ErrorOutlineIcon color="error" />
            </Grid>
            <Grid item>
              <Typography variant="body1">Please complete empty fields to continue</Typography>
            </Grid>
          </Grid>
        )}
        {!isNull(stationAddedError) && (
          <Grid container direction="row" justifyContent="center" spacing={1} marginTop={5}>
            <Grid item>
              <ErrorOutlineIcon color="error" />
            </Grid>
            <Grid item>
              <Typography variant="body1">Station already exists</Typography>
            </Grid>
          </Grid>
        )} */}
    </Grid>
  )
}

export default React.memo(StationForm)
