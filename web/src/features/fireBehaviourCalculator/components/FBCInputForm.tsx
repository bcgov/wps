import React, { useEffect } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { FormControl, InputLabel, Select, TextField } from '@material-ui/core'
import { useDispatch } from 'react-redux'
import { getStations } from 'api/stationAPI'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { isGrassFuelType } from '../utils'

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
  fuelType: string
  setFuelType: (fuelType: string) => void
  grassCurePercentage: number | null
  setGrassCurePercentage: (percentage: number | null) => void
  stationMenuItems: JSX.Element[]
  fuelTypeMenuItems: JSX.Element[]
}

const FBCInputForm = (props: FBCInputFormProps) => {
  const classes = useStyles()
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-station-select">Weather Station</InputLabel>
        <Select
          labelId="fbc-station-select"
          id="station-select"
          value={props.stationsOfInterest}
          variant="outlined"
          onChange={event => {
            props.setStationsOfInterest(event.target.value as number)
          }}
        >
          {props.stationMenuItems}
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-fuel-type-select">Fuel Type</InputLabel>
        <Select
          labelId="fbc-fuel-type-select"
          id="fuel-type-select"
          value={props.fuelType}
          variant="outlined"
          onChange={event => {
            props.setFuelType(event.target.value as string)
          }}
        >
          {props.fuelTypeMenuItems}
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <TextField
          id="input-grass-cure"
          type="number"
          label="Grass Cure %"
          variant="outlined"
          required={isGrassFuelType(props.fuelType)}
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
    </div>
  )
}

export default React.memo(FBCInputForm)
