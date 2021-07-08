import { FormControl, makeStyles } from '@material-ui/core'
import { GeoJsonStation, getStations } from 'api/stationAPI'
import {
  selectFireBehaviourCalcResult,
  selectFireBehaviourStationsLoading,
  selectFireWeatherStations
} from 'app/rootReducer'
import { Button, Container, PageHeader } from 'components'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { DateTime } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import DatePicker from './components/DatePicker'
import FBCInputGrid, { FBCInputRow, GridMenuOption } from './components/FBCInputGrid'
import FBCResultTable from './components/FBCResultTable'
import { FuelTypes } from './fuelTypes'
import { fetchFireBehaviourStations } from './slices/fireBehaviourCalcSlice'
import { isValidFuelSetting } from './utils'

export const FireBehaviourCalculatorGrid: React.FunctionComponent = () => {
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())
  // eslint-disable-next-line
  const [stationsOfInterest, setStationsOfInterest] = useState(322)
  // eslint-disable-next-line
  const [fuelType, setFuelType] = useState('')
  // eslint-disable-next-line
  const [grassCurePercentage, setGrassCurePercentage] = useState<number | null>(null)

  const { stations } = useSelector(selectFireWeatherStations)

  // Input stuff

  // eslint-disable-next-line
  const [rowId, setRowId] = useState(1)
  const stationMenuOptions: GridMenuOption[] = (stations as GeoJsonStation[]).map(
    station => ({
      value: station.properties.code,
      label: `${station.properties.name} - ${station.properties.code}`
    })
  )

  const fuelTypeMenuOptions: GridMenuOption[] = Object.entries(FuelTypes.get()).map(
    ([key, value]) => ({
      value: key,
      label: value.friendlyName
    })
  )
  // eslint-disable-next-line
  const [rows, setRows] = useState<FBCInputRow[]>([
    {
      id: rowId,
      weatherStation: stationMenuOptions[0],
      fuelType: fuelTypeMenuOptions[0],
      grassCure: 0
    }
  ])

  const addStationOfInterest = () => {
    setRowId(rowId + 1)
    const newRow = {
      id: rowId,
      weatherStation: stationMenuOptions[0],
      fuelType: fuelTypeMenuOptions[0],
      grassCure: 0
    }
    setRows([...rows, newRow])
  }
  const { fireBehaviourResultStations } = useSelector(selectFireBehaviourCalcResult)

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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
              onClick={addStationOfInterest}
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
          <FBCInputGrid
            stationMenuOptions={stationMenuOptions}
            fuelTypeMenuOptions={fuelTypeMenuOptions}
            rows={rows}
          />
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
