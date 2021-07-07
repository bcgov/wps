import React, { useEffect } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { FormControl, InputLabel, MenuItem, Select, TextField } from '@material-ui/core'
import DatePicker from './DatePicker'
import {
  selectFireBehaviourStationsLoading,
  selectFireWeatherStations
} from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import { GeoJsonStation, getStations } from 'api/stationAPI'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { FuelTypes } from '../fuelTypes'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { fetchFireBehaviourStations } from '../slices/fireBehaviourCalcSlice'
import { isNull } from 'lodash'

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
  grassCurePercentage: number | null
  setGrassCurePercentage: (percentage: number | null) => void
}

const FBCInputForm = (props: FBCInputFormProps) => {
  const classes = useStyles()
  const dispatch = useDispatch()

  const { stations } = useSelector(selectFireWeatherStations)

  const isGrassFuelType = () => props.fuelType === 'o1a' || props.fuelType === 'o1b'
  const isValidFuelSetting = () => {
    if (isGrassFuelType()) {
      return !isNull(props.grassCurePercentage)
    }
    return true
  }

  const stationMenuItems = (stations as GeoJsonStation[]).map(
    (station: GeoJsonStation, index) => (
      <MenuItem value={station.properties.code} key={index}>
        {station.properties.code} - {station.properties.name}
      </MenuItem>
    )
  )

  const fuelTypeMenuItems = Object.entries(FuelTypes.get()).map(([key, value], index) => (
    <MenuItem value={key} key={index}>
      {value.friendlyName}
    </MenuItem>
  ))

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-station-input">Weather Station</InputLabel>
        <Select
          labelId="fbc-station-select"
          id="station-select"
          value={props.stationsOfInterest}
          variant="outlined"
          onChange={event => {
            props.setStationsOfInterest(event.target.value as number)
          }}
        >
          {stationMenuItems}
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <DatePicker date={props.dateOfInterest} onChange={props.setDateOfInterest} />
      </FormControl>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-fuel-input">Input Fuel Type</InputLabel>
        <Select
          labelId="fbc-fuel-type-select"
          id="fuel-type-select"
          value={props.fuelType}
          variant="outlined"
          onChange={event => {
            props.setFuelType(event.target.value as string)
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
          required={isGrassFuelType()}
          onChange={e => {
            const value = e.currentTarget.value

            if (value) {
              props.setGrassCurePercentage((value as unknown) as number)
            } else {
              props.setGrassCurePercentage(null)
            }
          }}
        />
      </FormControl>
      <FormControl className={classes.formControl}>
        <GetWxDataButton
          disabled={!isValidFuelSetting()}
          onBtnClick={() => {
            dispatch(
              fetchFireBehaviourStations(
                props.dateOfInterest,
                [props.stationsOfInterest],
                props.fuelType,
                props.grassCurePercentage
              )
            )
          }}
          selector={selectFireBehaviourStationsLoading}
          buttonLabel="Calculate"
        />
      </FormControl>
    </div>
  )
}

export default React.memo(FBCInputForm)
