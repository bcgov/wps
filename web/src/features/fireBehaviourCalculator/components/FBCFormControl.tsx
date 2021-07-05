import React, { useEffect, useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { DateTime } from 'luxon'
import { FormControl, InputLabel, MenuItem, Select, TextField } from '@material-ui/core'
import { Button } from 'components'
import DatePicker from './DatePicker'
import { selectFireWeatherStations } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import { GeoJsonStation, getStations } from 'api/stationAPI'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { FuelTypes } from '../fuelTypes'

const useStyles = makeStyles(theme => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 180
  }
}))

interface FBCInputFormProps {
  testId?: string
}

const FBCInputForm = (props: FBCInputFormProps) => {
  const classes = useStyles()
  const dispatch = useDispatch()

  const { stations } = useSelector(selectFireWeatherStations)

  const stationMenuItems = (stations as GeoJsonStation[]).map(
    (station: GeoJsonStation) => (
      <MenuItem value={station.properties.code}>
        {station.properties.code} - {station.properties.name}
      </MenuItem>
    )
  )

  const fuelTypeMenuItems = FuelTypes.get().map(fuelType => (
    <MenuItem value={fuelType.name}>{fuelType.friendlyName}</MenuItem>
  ))

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-date-input">Weather Station</InputLabel>
        <Select labelId="fbc-date-select" id="date-select" value={322} variant="outlined">
          {stationMenuItems}
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <DatePicker date={dateOfInterest} onChange={setDateOfInterest} />
      </FormControl>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-date-input">Input Fuel Type</InputLabel>
        <Select
          labelId="fbc-weather-fuel-type-select"
          id="fuel-type-select"
          value={'c2'}
          variant="outlined"
        >
          {fuelTypeMenuItems}
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <TextField id="input-grass-cure" label="Input Grass Cure %" variant="outlined" />
      </FormControl>
      <FormControl className={classes.formControl}>
        <Button
          data-testid="get-wx-data-button"
          variant="contained"
          color="primary"
          spinnercolor="white"
        >
          Calculate
        </Button>
      </FormControl>
    </div>
  )
}

export default React.memo(FBCInputForm)
