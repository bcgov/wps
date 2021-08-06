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
import DatePicker from 'features/fireBehaviourCalculator/components/DatePicker'
import FBCInputGrid, {
  GridMenuOption,
  FBCInputRow
} from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import { FuelTypes } from 'features/fireBehaviourCalculator/fuelTypes'
import { fetchFireBehaviourStations } from 'features/fireBehaviourCalculator/slices/fireBehaviourCalcSlice'
import {
  getRowsFromUrlParams,
  getMostRecentIdFromRows,
  getUrlParamsFromRows
} from 'features/fireBehaviourCalculator/utils'
import { FBCStation } from 'api/fbCalcAPI'

export const FireBehaviourCalculator: React.FunctionComponent = () => {
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
  const [rows, setRows] = useState<FBCInputRow[]>(rowsFromQuery)
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

  const updateRow = (id: GridRowId, updatedRow: FBCInputRow, dispatchUpdate = true) => {
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
    disclaimer: {
      borderLeft: '6px solid #FCBA19',
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
        {loading ? (
          <CircularProgress className={classes.spinner} />
        ) : (
          <React.Fragment>
            <FBCInputGrid
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
          </React.Fragment>
        )}
        <Paper className={classes.disclaimer}>
          <div>
            <h4>Disclaimers:</h4>
            <p>
              Forecasted weather outputs are for 13:00 and FWI Indices are for 17:00 PDT.
              These fire behaviour calculations assume flat terrain.
            </p>
            <p>
              Weather and fire behaviour indices are sourced from the Wildfire One API.
            </p>
            <p>
              Values are calculated using the{' '}
              <a href="https://r-forge.r-project.org/projects/cffdrs/">
                Canadian Forest Fire Danger Rating System R Library
              </a>{' '}
              and are intended to provide general guidance for Fire Behaviour Advisories.
            </p>
            <p>
              Constants for crown fuel load are taken from "Development and Structure of
              the Canadian Forest Fire Behaviour Prediction System" from Forestry Canada
              Fire Danger Group, Information Report ST-X-3, 1992.
            </p>
          </div>
        </Paper>
      </Container>
    </main>
  )
}
