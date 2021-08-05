import { CircularProgress, FormControl, makeStyles, Paper } from '@material-ui/core'
import { GridRowId } from '@material-ui/data-grid'
import { GeoJsonStation, getStations, StationSource } from 'api/stationAPI'
import { selectFireBehaviourCalcResult, selectFireWeatherStations } from 'app/rootReducer'
import { Button, Container, PageHeader } from 'components'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { DateTime } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useHistory, useLocation } from 'react-router-dom'
import { filter } from 'lodash'
import DatePicker from 'features/fbaCalculator/components/DatePicker'
import FBAInputGrid, {
  GridMenuOption,
  FBAInputRow
} from 'features/fbaCalculator/components/FBAInputGrid'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { fetchFireBehaviourStations } from 'features/fbaCalculator/slices/fbaCalculatorSlice'
import {
  getRowsFromUrlParams,
  getMostRecentIdFromRows,
  getUrlParamsFromRows
} from 'features/fbaCalculator/utils'
import { FBCStation } from 'api/fbCalcAPI'

export const FireBehaviourAdvisoryCalculator: React.FunctionComponent = () => {
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())

  const { stations } = useSelector(selectFireWeatherStations)

  const stationMenuOptions: GridMenuOption[] = (stations as GeoJsonStation[]).map(
    station => ({
      value: String(station.properties.code),
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
  const [rows, setRows] = useState<FBAInputRow[]>(rowsFromQuery)
  const lastId = getMostRecentIdFromRows(rows)

  const [rowId, setRowId] = useState(lastId + 1)
  const [selected, setSelected] = useState<number[]>([])

  const { fireBehaviourResultStations, loading } = useSelector(
    selectFireBehaviourCalcResult
  )
  const [calculatedResults, setCalculatedResults] = useState<FBCStation[]>(
    fireBehaviourResultStations
  )

  useEffect(() => {
    setCalculatedResults(fireBehaviourResultStations)
  }, [fireBehaviourResultStations]) // eslint-disable-line react-hooks/exhaustive-deps

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
    const updatedCalculateRows = filter(calculatedResults, (_, i) => !selectedSet.has(i))
    setRows(unselectedRows)
    setCalculatedResults(updatedCalculateRows)
    updateQueryParams(getUrlParamsFromRows(unselectedRows))
    setSelected([])
  }

  const updateRow = (id: GridRowId, updatedRow: FBAInputRow, dispatchUpdate = true) => {
    const newRows = [...rows]

    // rowId is the row array index
    newRows[id as number] = updatedRow
    setRows(newRows)
    if (dispatchUpdate) {
      updateQueryParams(getUrlParamsFromRows(newRows))
      dispatch(fetchFireBehaviourStations(dateOfInterest, newRows))
    }
  }

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const updateQueryParams = (queryParams: string) => {
    history.push({
      search: queryParams
    })
  }

  useEffect(() => {
    const rows = getRowsFromUrlParams(location.search)
    setRows(rows)
    const mostRecentId = getMostRecentIdFromRows(rows)
    setRowId(mostRecentId + 1)

    if (rows.length > 0) {
      dispatch(fetchFireBehaviourStations(dateOfInterest, rows))
    }
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  const useStyles = makeStyles(theme => ({
    formControl: {
      margin: theme.spacing(1),
      minWidth: 210
    },
    criticalHours: {
      borderLeft: '6px solid #e6ebf0',
      padding: '10px',
      marginBottom: theme.spacing(8)
    },
    spinner: {
      position: 'absolute',
      left: '50%',
      marginLeft: -10,
      top: '50%',
      marginTop: -10
    }
  }))

  const autoUpdateHandler = () => {
    dispatch(fetchFireBehaviourStations(dateOfInterest, rows))
  }

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
            <DatePicker
              date={dateOfInterest}
              onChange={setDateOfInterest}
              autoUpdateHandler={autoUpdateHandler}
            />
          </FormControl>
          <FormControl className={classes.formControl}>
            <Button
              data-testid="add-row"
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
              data-testid="remove-rows"
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
        {loading ? (
          <CircularProgress className={classes.spinner} />
        ) : (
          <React.Fragment>
            <FBAInputGrid
              stationOptions={stationMenuOptions}
              fuelTypeOptions={fuelTypeMenuOptions}
              inputRows={rows}
              updateRow={updateRow}
              selected={selected}
              updateSelected={(selectedRows: number[]) => {
                setSelected(selectedRows)
              }}
              calculatedResults={calculatedResults}
              autoUpdateHandler={autoUpdateHandler}
            />
            <Paper className={classes.criticalHours}>
              <div>
                <h4>
                  Forecasted weather outputs are for 13:00 and FWI Indices for 17:00 PDT.
                </h4>
                <p>These fire behaviour calculations assume flat terrain.</p>
              </div>
            </Paper>
          </React.Fragment>
        )}
      </Container>
    </main>
  )
}
