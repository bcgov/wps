import { FormControl, makeStyles } from '@material-ui/core'
import { GridRowId } from '@material-ui/data-grid'
import { GeoJsonStation, getStations, StationSource } from 'api/stationAPI'
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
import { some } from 'lodash'
import DatePicker from 'features/fireBehaviourCalculator/components/DatePicker'
import FBCInputGrid, {
  GridMenuOption,
  FBCInputRow
} from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import FBCResultTable from 'features/fireBehaviourCalculator/components/FBCResultTable'
import { FuelTypes } from 'features/fireBehaviourCalculator/fuelTypes'
import { fetchFireBehaviourStations } from 'features/fireBehaviourCalculator/slices/fireBehaviourCalcSlice'
import {
  getRowsFromUrlParams,
  getMostRecentIdFromRows,
  getUrlParamsFromRows
} from 'features/fireBehaviourCalculator/utils'
import { shouldDisableCalculate } from 'features/fireBehaviourCalculator/validation'

export const FireBehaviourCalculator: React.FunctionComponent = () => {
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())

  const { stations } = useSelector(selectFireWeatherStations)

  const stationMenuOptions: GridMenuOption[] = (stations as GeoJsonStation[]).map(
    station => ({
      value: station.properties.code,
      label: `${station.properties.name} (${station.properties.code})`
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
  const [selected, setSelected] = useState<number[]>([])

  const addStation = () => {
    const newRowId = rowId + 1
    setRowId(newRowId)
    const newRow = {
      id: rowId,
      weatherStation: undefined,
      fuelType: undefined,
      grassCure: undefined,
      windSpeed: undefined
    }
    const newRows = [...rows, newRow]
    setRows(newRows)
    updateQueryParams(getUrlParamsFromRows(newRows))
  }

  const deleteSelectedStations = () => {
    const selectedSet = new Set<number>(selected)
    const unselectedRows = rows.filter(row => !selectedSet.has(row.id))
    console.log(unselectedRows)
    setRows(unselectedRows)
    updateQueryParams(getUrlParamsFromRows(unselectedRows))
    setSelected([])
  }

  const updateRow = (rowId: GridRowId, updatedRow: FBCInputRow) => {
    const newRows = [...rows]

    // rowId is the row array index
    newRows[rowId as number] = updatedRow
    setRows(newRows)
    updateQueryParams(getUrlParamsFromRows(newRows))
  }
  const { fireBehaviourResultStations } = useSelector(selectFireBehaviourCalcResult)

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const updateQueryParams = (queryParams: string) => {
    history.push({
      search: queryParams
    })
  }

  useEffect(() => {
    const rowsFromQuery = getRowsFromUrlParams(location.search)
    setRows(rowsFromQuery)
    const lastId = getMostRecentIdFromRows(rows)
    setRowId(lastId + 1)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  const disableCalculateButton =
    rows.length === 0 ||
    some(rows, row => {
      return shouldDisableCalculate(row)
    })

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
        <h1>
          {/* (🔥🦇) */}
          Fire Behaviour Advisory Tool <b style={{ color: 'Red' }}>Prototype</b>
        </h1>
        <div>
          <FormControl className={classes.formControl}>
            <DatePicker date={dateOfInterest} onChange={setDateOfInterest} />
          </FormControl>
          <FormControl className={classes.formControl}>
            <Button
              variant="contained"
              color="primary"
              spinnercolor="white"
              onClick={addStation}
            >
              Add Row
            </Button>
          </FormControl>
          <FormControl className={classes.formControl}>
            <Button
              disabled={rows.length === 0}
              variant="contained"
              color="primary"
              spinnercolor="white"
              onClick={deleteSelectedStations}
            >
              Remove Row(s)
            </Button>
          </FormControl>
        </div>
        <br />
        <div style={{ display: 'flex', height: '100%' }}>
          <FBCInputGrid
            stationOptions={stationMenuOptions}
            fuelTypeOptions={fuelTypeMenuOptions}
            rows={rows}
            updateRow={updateRow}
            selected={selected}
            updateSelected={(selected: number[]) => {
              setSelected(selected)
            }}
          />
        </div>
        <FormControl className={classes.formControl}>
          <GetWxDataButton
            disabled={disableCalculateButton}
            onBtnClick={() => {
              dispatch(fetchFireBehaviourStations(dateOfInterest, rows))
            }}
            selector={selectFireBehaviourStationsLoading}
            buttonLabel="Calculate"
          />
        </FormControl>
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
