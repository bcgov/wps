import React, { useEffect, useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { DateTime } from 'luxon'
import { FormControl, InputLabel, MenuItem, Select, TextField } from '@material-ui/core'
import { Button } from 'components'
import DatePicker from './DatePicker'
import { selectFireWeatherStations } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import { getDetailedStations, StationSource } from 'api/stationAPI'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'

const useStyles = makeStyles(theme => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 180
  },
  timeOfInterest: {
    marginRight: 16
  }
}))

interface FBCInputControlProps {
  testId?: string
}

const FBCInputControls = (props: FBCInputControlProps) => {
  const classes = useStyles()
  const dispatch = useDispatch()

  const { stations } = useSelector(selectFireWeatherStations)
  console.log(stations)

  useEffect(() => {
    dispatch(fetchWxStations(getDetailedStations, StationSource.local_storage))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-date-input">Weather Station</InputLabel>
        <Select labelId="fbc-date-select" id="date-select" value={322} variant="outlined">
          <MenuItem value={10}>Ten</MenuItem>
          <MenuItem value={20}>Twenty</MenuItem>
          <MenuItem value={30}>Thirty</MenuItem>
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
          value={'C5'}
          variant="outlined"
        >
          <MenuItem value={10}>C5</MenuItem>
          <MenuItem value={20}>C6</MenuItem>
          <MenuItem value={30}>C7</MenuItem>
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

export default React.memo(FBCInputControls)
