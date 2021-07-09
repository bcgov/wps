import { FormControl, makeStyles } from '@material-ui/core'
import { GridRowId } from '@material-ui/data-grid'
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
import { useHistory, useLocation } from 'react-router-dom'
import DatePicker from './components/DatePicker'
import FBCInputGrid, { FBCInputRow, GridMenuOption } from './components/FBCInputGrid'
import FBCResultTable from './components/FBCResultTable'
import { FuelTypes } from './fuelTypes'
import { fetchFireBehaviourStations } from './slices/fireBehaviourCalcSlice'
import {
  getMostRecentIdFromRows,
  getRowsFromUrlParams,
  isValidFuelSetting
} from './utils'

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
  const location = useLocation()
  const history = useHistory()

  const rowsFromQuery = getRowsFromUrlParams(location.search)
  const [rows, setRows] = useState<FBCInputRow[]>(rowsFromQuery)
  const lastId = getMostRecentIdFromRows(rows)

  const [rowId, setRowId] = useState(lastId + 1)

  const addStationOfInterest = () => {
    const newRowId = rowId + 1
    setRowId(newRowId)
    const newRow = {
      id: rowId,
      weatherStation: stationMenuOptions[0].value.toString(),
      fuelType: fuelTypeMenuOptions[0].value.toString(),
      grassCure: 0
    }
    setRows([...rows, newRow])
  }

  const updateRow = (rowId: GridRowId, updatedRow: FBCInputRow) => {
    const newRows = [...rows]

    // rowId is the row array index
    newRows[rowId as number] = updatedRow
    setRows(newRows)
  }
  const { fireBehaviourResultStations } = useSelector(selectFireBehaviourCalcResult)

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const updateQueryParams = () => {
    history.push({
      search: ''
    })
  }

  useEffect(() => {
    const rowsFromQuery = getRowsFromUrlParams(location.search)
    setRows(rowsFromQuery)
    const lastId = getMostRecentIdFromRows(rows)
    setRowId(lastId + 1)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

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
            updateRow={updateRow}
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
