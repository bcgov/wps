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
  stationsOfInterest: number
  setStationsOfInterest: (stations: number) => void
  dateOfInterest: string
  setDateOfInterest: (date: string) => void
  fuelType: string
  setFuelType: (fuelType: string) => void
  grassCurePercentage: number
  setGrassCurePercentage: (percentage: number) => void
}

const FBCInputForm = (props: FBCInputFormProps) => {
  const classes = useStyles()
  const dispatch = useDispatch()

  const { stations } = useSelector(selectFireWeatherStations)

  const stationMenuItems = (stations as GeoJsonStation[]).map(
    (station: GeoJsonStation, index) => (
      <MenuItem value={station.properties.code} key={index}>
        {station.properties.code} - {station.properties.name}
      </MenuItem>
    )
  )

  const fuelTypeMenuItems = FuelTypes.get().map((fuelType, index) => (
    <MenuItem value={fuelType.name} key={index}>
      {fuelType.friendlyName}
    </MenuItem>
  ))

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-station-input">Weather Station</InputLabel>
        <Select
          labelId="fbc-station-select"
          id="station-select"
          value={props.stationsOfInterest}
          variant="outlined"
          onChange={e => {
            const value = e.currentTarget.value

            if (value) {
              props.setStationsOfInterest(value as number)
            }
          }}
        >
          {stationMenuItems}
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <DatePicker date={dateOfInterest} onChange={setDateOfInterest} />
      </FormControl>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-fuel-input">Input Fuel Type</InputLabel>
        <Select
          labelId="fbc-fuel-type-select"
          id="fuel-type-select"
          value={props.fuelType}
          variant="outlined"
          onChange={e => {
            const value = e.currentTarget.value

            if (value) {
              props.setFuelType(value as string)
            }
          }}
        >
          {fuelTypeMenuItems}
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <TextField
          id="input-grass-cure"
          type="number"
          label="Input Grass Cure %"
          variant="outlined"
          onChange={e => {
            const value = e.currentTarget.value

            if (value) {
              props.setGrassCurePercentage((value as unknown) as number)
            }
          }}
        />
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
