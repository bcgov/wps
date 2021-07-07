import { FormControl, makeStyles, MenuItem } from '@material-ui/core'
import { GeoJsonStation } from 'api/stationAPI'
import {
  selectFireBehaviourCalcResult,
  selectFireBehaviourStationsLoading,
  selectFireWeatherStations
} from 'app/rootReducer'
import { Button, Container, PageHeader } from 'components'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { DateTime } from 'luxon'
import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import DatePicker from './components/DatePicker'
import FBCInputGrid from './components/FBCInputGrid'
import FBCResultTable from './components/FBCResultTable'
import { FuelTypes } from './fuelTypes'
import { fetchFireBehaviourStations } from './slices/fireBehaviourCalcSlice'
import { StationConfig } from './stationConfig'
import { isValidFuelSetting } from './utils'

export const FireBehaviourCalculatorGrid: React.FunctionComponent = () => {
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())
  // eslint-disable-next-line
  const [stationsOfInterest, setStationsOfInterest] = useState(322)
  // eslint-disable-next-line
  const [fuelType, setFuelType] = useState('')
  // eslint-disable-next-line
  const [grassCurePercentage, setGrassCurePercentage] = useState<number | null>(null)
  const [stationConfigs, setStations] = useState<Set<StationConfig>>(
    new Set([new StationConfig()])
  )

  const { fireBehaviourResultStations } = useSelector(selectFireBehaviourCalcResult)

  const { stations } = useSelector(selectFireWeatherStations)
  // eslint-disable-next-line
  const stationMenuItems = (stations as GeoJsonStation[]).map(
    (station: GeoJsonStation, index) => (
      <MenuItem value={station.properties.code} key={index}>
        {station.properties.code} - {station.properties.name}
      </MenuItem>
    )
  )
  // eslint-disable-next-line
  const fuelTypeMenuItems = Object.entries(FuelTypes.get()).map(([key, value], index) => (
    <MenuItem value={key} key={index}>
      {value.friendlyName}
    </MenuItem>
  ))

  const useStyles = makeStyles(theme => ({
    formControl: {
      margin: theme.spacing(1),
      minWidth: 180
    }
  }))

  const classes = useStyles()

  const dispatch = useDispatch()

  return (
    <main>
      <PageHeader
        title="Predictive Services Unit"
        productName="Predictive Services Unit"
      />
      <Container maxWidth={'xl'}>
        <h1>Fire Behavior Calculator Prototype</h1>
        <div>
          <FormControl className={classes.formControl}>
            <DatePicker date={dateOfInterest} onChange={setDateOfInterest} />
          </FormControl>
          <FormControl className={classes.formControl}>
            <Button
              variant="contained"
              color="primary"
              spinnercolor="white"
              onClick={() => {
                stationConfigs.add(new StationConfig())
                setStations(new Set(stationConfigs))
              }}
            >
              Add Station
            </Button>
          </FormControl>
          <FormControl className={classes.formControl}>
            <GetWxDataButton
              disabled={!isValidFuelSetting(fuelType, grassCurePercentage)}
              onBtnClick={() => {
                dispatch(
                  fetchFireBehaviourStations(
                    dateOfInterest,
                    [stationsOfInterest],
                    fuelType,
                    grassCurePercentage
                  )
                )
              }}
              selector={selectFireBehaviourStationsLoading}
              buttonLabel="Calculate"
            />
          </FormControl>
        </div>
        <br />
        <div style={{ display: 'flex', height: '100%' }}>
          <FBCInputGrid />
        </div>
        {fireBehaviourResultStations.length > 0 && (
          <FBCResultTable
            testId="fb-calc-result-table"
            fireBehaviourResultStations={fireBehaviourResultStations}
          />
        )}
      </Container>
    </main>
  )
}
