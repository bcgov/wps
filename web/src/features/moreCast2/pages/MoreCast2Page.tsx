import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AlertColor, FormControl, Grid, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import { FireCenter, FireCenterStation } from 'api/fbaAPI'
import {
  DEFAULT_MODEL_TYPE,
  ForecastActionChoice,
  ForecastActionChoices,
  ForecastActionType,
  ModelChoice,
  ModelOptions,
  ModelType,
  submitMoreCastForecastRecords
} from 'api/moreCast2API'
import {
  selectAuthentication,
  selectColumnModelStationPredictions,
  selectColumnYesterdayDailies,
  selectFireCenters,
  selectModelStationPredictions,
  selectMoreCast2Forecasts,
  selectObservedDailies,
  selectYesterdayDailies
} from 'app/rootReducer'
import { AppDispatch } from 'app/store'
import { fetchFireCenters } from 'commonSlices/fireCentersSlice'
import { GeneralHeader } from 'components'
import { MORE_CAST_2_DOC_TITLE, MORE_CAST_2_NAME } from 'utils/constants'
import MoreCast2DataGrid from 'features/moreCast2/components/MoreCast2DataGrid'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { getModelStationPredictions } from 'features/moreCast2/slices/modelSlice'
import {
  createDateInterval,
  fillInTheModelBlanks,
  filterRowsByModelType,
  parseForecastsHelper,
  parseModelsForStationsHelper,
  parseObservedDailiesForStationsHelper,
  parseObservedDailiesFromResponse,
  replaceColumnValuesFromPrediction
} from 'features/moreCast2/util'
import {
  fillInTheYesterdayDailyBlanks,
  parseYesterdayDailiesForStationsHelper,
  replaceColumnValuesFromYesterdayDaily
} from 'features/moreCast2/yesterdayDailies'
import { getYesterdayStationDailies } from 'features/moreCast2/slices/yesterdayDailiesSlice'
import { getObservedStationDailies } from 'features/moreCast2/slices/observedDailiesSlice'
import SaveForecastButton from 'features/moreCast2/components/SaveForecastButton'
import MoreCase2DateRangePicker from 'features/moreCast2/components/MoreCast2DateRangePicker'
import { ROLES } from 'features/auth/roles'
import { DateRange } from 'components/dateRangePicker/types'
import { GridColDef } from '@mui/x-data-grid'
import { getColumnModelStationPredictions } from 'features/moreCast2/slices/columnModelSlice'
import { getColumnYesterdayDailies } from 'features/moreCast2/slices/columnYesterdaySlice'
import { getMoreCast2Forecasts } from 'features/moreCast2/slices/moreCast2ForecastsSlice'
import MoreCast2Snackbar from 'features/moreCast2/components/MoreCast2Snackbar'
import ForecastActionDropdown from 'features/moreCast2/components/ForecastActionDropdown'
import { objectTraps } from 'immer/dist/internal'

const useStyles = makeStyles(theme => ({
  content: {
    display: 'flex',
    flexGrow: 1,
    maxHeight: 'calc(100vh - 71.5px)',
    borderTop: '1px solid black',
    overflowY: 'hidden'
  },
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  observations: {
    display: 'flex',
    flexGrow: 1,
    flexDirection: 'column'
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    overflowY: 'hidden'
  },
  sidePanel: {
    display: 'flex',
    width: '375px',
    borderRight: '1px solid black',
    overflowY: 'auto'
  },
  actionButtonContainer: {
    marginTop: 15
  }
}))

const DEFAULT_MODEL_TYPE_KEY = 'defaultModelType'
const DEFAULT_FIRE_CENTER_KEY = 'preferredMoreCast2FireCenter'

const FORECAST_ERROR_MESSAGE = 'The forecast was not saved; an unexpected error occurred.'
const FORECAST_SAVED_MESSAGE = 'Forecast was successfully saved.'
const FORECAST_WARN_MESSAGE = 'A forecast cannot contain N/A values.'

const MoreCast2Page = () => {
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()
  const { fireCenters } = useSelector(selectFireCenters)
  const { stationPredictions } = useSelector(selectModelStationPredictions)
  const { yesterdayDailies } = useSelector(selectYesterdayDailies)
  const { observedDailies } = useSelector(selectObservedDailies)
  const { moreCast2Forecasts } = useSelector(selectMoreCast2Forecasts)
  const { roles, isAuthenticated } = useSelector(selectAuthentication)

  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)
  const [selectedStations, setSelectedStations] = useState<FireCenterStation[]>([])
  const [modelType, setModelType] = useState<ModelType>(
    (localStorage.getItem(DEFAULT_MODEL_TYPE_KEY) as ModelType) || DEFAULT_MODEL_TYPE
  )
  const [snackbarMessage, setSnackbarMessage] = useState('')
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const [snackbarSeverity, setSnackbarSeverity] = useState<AlertColor>('success')

  const currentTimeIsBeforeNoon = DateTime.now().hour < 13 ? true : false
  let startDateTime
  if (currentTimeIsBeforeNoon) {
    startDateTime = DateTime.now().minus({ days: 3 })
  } else {
    startDateTime = DateTime.now().minus({ days: 2 })
  }
  const endDateTime = DateTime.now().plus({ days: 2 })
  const [fromTo, setFromTo] = useState<DateRange>({
    startDate: startDateTime.toJSDate(),
    endDate: endDateTime.toJSDate()
  })
  const [forecastRows, setForecastRows] = useState<MoreCast2ForecastRow[]>([])
  const [stationPredictionsAsMoreCast2ForecastRows, setStationPredictionsAsMoreCast2ForecastRows] = useState<
    MoreCast2ForecastRow[]
  >([])
  const [observedRows, setObservedRows] = useState<MoreCast2ForecastRow[]>([])
  const [rowsToDisplay, setRowsToDisplay] = useState<MoreCast2ForecastRow[]>([])
  const [forecastAction, setForecastAction] = useState<ForecastActionType>(ForecastActionChoices[0])
  const [forecastIsDirty, setForecastIsDirty] = useState(false)
  const [forecastsAsMoreCast2ForecastRows, setForecastsAsMoreCast2ForecastRows] = useState<MoreCast2ForecastRow[]>([])
  const [dateInterval, setDateInterval] = useState<string[]>([])

  const { colPrediction } = useSelector(selectColumnModelStationPredictions)
  const { colYesterdayDailies } = useSelector(selectColumnYesterdayDailies)

  const [clickedColDef, setClickedColDef] = React.useState<GridColDef | null>(null)
  const updateColumnWithModel = (modelType: ModelType, colDef: GridColDef) => {
    if (modelType == ModelChoice.YESTERDAY) {
      dispatch(
        getColumnYesterdayDailies(
          stationPredictionsAsMoreCast2ForecastRows.map(s => s.stationCode),
          selectedStations,
          dateInterval,
          modelType,
          colDef.field as keyof MoreCast2ForecastRow,
          DateTime.fromJSDate(fromTo.startDate ? fromTo.startDate : new Date()).toISODate()
        )
      )
    } else {
      dispatch(
        getColumnModelStationPredictions(
          stationPredictionsAsMoreCast2ForecastRows.map(s => s.stationCode),
          modelType,
          colDef.field as keyof MoreCast2ForecastRow,
          DateTime.fromJSDate(fromTo.startDate ? fromTo.startDate : new Date()).toISODate(),
          DateTime.fromJSDate(fromTo.endDate ? fromTo.endDate : new Date()).toISODate()
        )
      )
    }
  }

  // Fetches observed/predicted values while in Create Forecast mode
  const fetchStationPredictions = () => {
    const stationCodes = fireCenter?.stations.map(station => station.code) || []
    if (isUndefined(fromTo.startDate) || isUndefined(fromTo.endDate)) {
      setForecastRows([])
      return
    }
    if (modelType == ModelChoice.YESTERDAY) {
      dispatch(getYesterdayStationDailies(stationCodes, DateTime.fromJSDate(fromTo.startDate).toISODate()))
    } else {
      dispatch(
        getModelStationPredictions(
          stationCodes,
          modelType,
          DateTime.fromJSDate(fromTo.startDate).toISODate(),
          DateTime.fromJSDate(fromTo.endDate).toISODate()
        )
      )
    }
  }

  const fetchStationObservedDailies = () => {
    const stationCodes = fireCenter?.stations.map(station => station.code) || []
    if (!isUndefined(fromTo.startDate)) {
      dispatch(getObservedStationDailies(stationCodes, DateTime.fromJSDate(fromTo.startDate).toISODate()))
    }
  }

  // Fetches previously submitted forecasts from the API database while in View/Edit Forecast mode
  const fetchForecasts = () => {
    const stationCodes = fireCenter?.stations.map(station => station.code) || []
    if (isUndefined(fromTo.startDate) || isUndefined(fromTo.endDate)) {
      setForecastRows([])
      return
    }
    dispatch(
      getMoreCast2Forecasts(DateTime.fromJSDate(fromTo.startDate), DateTime.fromJSDate(fromTo.endDate), stationCodes)
    )
  }

  useEffect(() => {
    dispatch(fetchFireCenters())
    document.title = MORE_CAST_2_DOC_TITLE
    fetchStationObservedDailies()
    fetchStationPredictions()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const workingRows = observedRows
    let uniqueArray = []
    const rowMatches = (row1: MoreCast2ForecastRow, row2: MoreCast2ForecastRow) =>
      row1.forDate === row2.forDate && row1.stationCode === row2.stationCode
    if (forecastAction === ForecastActionChoice.CREATE) {
      workingRows.concat(stationPredictionsAsMoreCast2ForecastRows)
      uniqueArray = workingRows.reduce((accumulator, currentObject) => {
        const objectExists = accumulator.some(rowMatches(currentObject))
        if (!objectExists) {
          return [...accumulator, currentObject]
        }
        return accumulator
      }, [])
    } else {
      forecastsAsMoreCast2ForecastRows.forEach(row => {
        const item = workingRows.find(obs => obs.forDate === row.forDate && obs.stationCode === row.stationCode)
        if (isUndefined(item)) {
          workingRows.push(row)
        }
      })
    }
    const visibleForecastRows = workingRows.filter(
      row => selectedStations.filter(station => station.code === row.stationCode).length
    )
    visibleForecastRows.sort((a, b) => (a.forDate > b.forDate ? 1 : -1))
    setRowsToDisplay(visibleForecastRows)
  }, [forecastRows, observedRows, stationPredictionsAsMoreCast2ForecastRows, selectedStations]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isNull(colPrediction)) {
      const newRows = replaceColumnValuesFromPrediction(
        stationPredictionsAsMoreCast2ForecastRows,
        selectedStations,
        dateInterval,
        colPrediction
      )
      setStationPredictionsAsMoreCast2ForecastRows(newRows)
    }
  }, [colPrediction]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isNull(colYesterdayDailies)) {
      const newRows = replaceColumnValuesFromYesterdayDaily(
        stationPredictionsAsMoreCast2ForecastRows,
        selectedStations,
        dateInterval,
        colYesterdayDailies
      )
      setStationPredictionsAsMoreCast2ForecastRows(newRows)
    }
  }, [colYesterdayDailies]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const findCenter = (id: string | null): FireCenter | undefined => {
      return fireCenters.find((center: FireCenter) => center.id.toString() == id)
    }
    if (fireCenters.length) {
      setFireCenter(findCenter(localStorage.getItem(DEFAULT_FIRE_CENTER_KEY)))
    }
  }, [fireCenters])

  useEffect(() => {
    if (fireCenter?.stations && fireCenter.stations.length && (isNull(fireCenter) || isUndefined(fireCenter))) {
      localStorage.removeItem(DEFAULT_FIRE_CENTER_KEY)
      return
    }
    if (!isUndefined(fireCenter) && !isNull(fireCenter)) {
      localStorage.setItem(DEFAULT_FIRE_CENTER_KEY, fireCenter.id.toString())
    }

    setSelectedStations(fireCenter?.stations ? fireCenter.stations.slice(0, 1) : [])
    fetchStationPredictions()
    fetchStationObservedDailies()
  }, [fireCenter]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isUndefined(modelType) && !isNull(modelType)) {
      localStorage.setItem(DEFAULT_MODEL_TYPE_KEY, modelType)
      fetchStationPredictions()
    } else {
      setForecastRows([])
    }
  }, [modelType]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isUndefined(fromTo.startDate) && !isUndefined(fromTo.endDate)) {
      const dates = createDateInterval(DateTime.fromJSDate(fromTo.startDate), DateTime.fromJSDate(fromTo.endDate))
      setDateInterval(dates)
    }

    if (forecastAction === ForecastActionChoice.CREATE) {
      if (!isUndefined(modelType) && !isNull(modelType)) {
        localStorage.setItem(DEFAULT_MODEL_TYPE_KEY, modelType)
        fetchStationObservedDailies()
        fetchStationPredictions()
      } else {
        setForecastRows([])
      }
    } else {
      // We're in view/edit mode
      fetchForecasts()
    }
  }, [fromTo.startDate, fromTo.endDate]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const predictions = fillInTheModelBlanks(fireCenter?.stations || [], stationPredictions, dateInterval, modelType)
    const newRows = parseModelsForStationsHelper(predictions)
    setStationPredictionsAsMoreCast2ForecastRows(newRows)
  }, [stationPredictions]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const completeDailies = fillInTheYesterdayDailyBlanks(fireCenter?.stations || [], yesterdayDailies, dateInterval)
    const newRows = parseYesterdayDailiesForStationsHelper(completeDailies)
    setStationPredictionsAsMoreCast2ForecastRows(newRows)
  }, [yesterdayDailies]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const completeDailies = fillInTheYesterdayDailyBlanks(fireCenter?.stations || [], observedDailies, dateInterval)
    const newRows = parseObservedDailiesForStationsHelper(completeDailies)
    setObservedRows(newRows)
  }, [observedDailies]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Handle the switch from create to edit mode and vice versa
    forecastAction === ForecastActionChoice.CREATE ? fetchStationPredictions() : fetchForecasts()
  }, [forecastAction]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const newRows = parseForecastsHelper(moreCast2Forecasts, fireCenter?.stations || [])
    setForecastsAsMoreCast2ForecastRows(newRows)
  }, [moreCast2Forecasts]) // eslint-disable-line react-hooks/exhaustive-deps

  // A valid, submittable forecast can't contain NaN for any values
  const forecastIsValid = () => {
    for (const forecastRow of forecastRows) {
      if (
        isNaN(forecastRow.precip.value) ||
        isNaN(forecastRow.rh.value) ||
        isNaN(forecastRow.temp.value) ||
        isNaN(forecastRow.windSpeed.value)
      ) {
        return false
      }
    }
    return true
  }

  const handleSaveClick = async () => {
    const rowsToSave: MoreCast2ForecastRow[] =
      forecastAction === ForecastActionChoice.CREATE
        ? forecastRows
        : filterRowsByModelType(forecastRows, ModelChoice.MANUAL)

    if (forecastIsValid()) {
      const result = await submitMoreCastForecastRecords(rowsToSave)
      if (result) {
        setSnackbarMessage(FORECAST_SAVED_MESSAGE)
        setSnackbarSeverity('success')
        setSnackbarOpen(true)
      } else {
        setSnackbarMessage(FORECAST_ERROR_MESSAGE)
        setSnackbarSeverity('error')
        setSnackbarOpen(true)
      }
    } else {
      setSnackbarMessage(FORECAST_WARN_MESSAGE)
      setSnackbarSeverity('warning')
      setSnackbarOpen(true)
    }
  }

  return (
    <div className={classes.root} data-testid="more-cast-2-page">
      <GeneralHeader padding="3em" spacing={0.985} title={MORE_CAST_2_NAME} productName={MORE_CAST_2_NAME} />
      <div className={classes.content}>
        <div className={classes.sidePanel}>
          <StationPanel
            fireCenter={fireCenter}
            fireCenters={fireCenters}
            selectedStations={selectedStations}
            setFireCenter={setFireCenter}
            setSelectedStations={setSelectedStations}
          />
        </div>
        <div className={classes.observations}>
          <Typography variant="h5">Forecasts</Typography>
          <Grid container spacing={1}>
            <Grid item xs={3}>
              <FormControl className={classes.formControl}>
                <ForecastActionDropdown
                  forecastActionOptions={ForecastActionChoices}
                  selectedForecastAction={forecastAction}
                  setForecastAction={setForecastAction}
                />
              </FormControl>
            </Grid>
            {
              // Only show the weather model dropdown when creating new forecasts
              forecastAction === ForecastActionChoice.CREATE && (
                <Grid item xs={3}>
                  <FormControl className={classes.formControl}>
                    <WeatherModelDropdown
                      weatherModelOptions={ModelOptions}
                      selectedModelType={modelType}
                      setSelectedModelType={setModelType}
                    />
                  </FormControl>
                </Grid>
              )
            }
            <Grid item xs={3}>
              <MoreCase2DateRangePicker dateRange={fromTo} setDateRange={setFromTo} />
            </Grid>
            <Grid item xs={2}>
              <FormControl className={classes.actionButtonContainer}>
                <SaveForecastButton
                  enabled={
                    roles.includes(ROLES.MORECAST_2.WRITE_FORECAST) &&
                    isAuthenticated &&
                    forecastRows.length > 0 &&
                    (forecastAction === ForecastActionChoice.CREATE || forecastIsDirty)
                  }
                  label={forecastAction === ForecastActionChoice.CREATE ? 'Save Forecast' : 'Update Forecast'}
                  onClick={handleSaveClick}
                />
              </FormControl>
            </Grid>
          </Grid>
          <MoreCast2DataGrid
            rows={rowsToDisplay}
            clickedColDef={clickedColDef}
            onCellEditStop={setForecastIsDirty}
            setClickedColDef={setClickedColDef}
            updateColumnWithModel={updateColumnWithModel}
          />
          <MoreCast2Snackbar
            autoHideDuration={6000}
            handleClose={() => setSnackbarOpen(!snackbarOpen)}
            open={snackbarOpen}
            message={snackbarMessage}
            severity={snackbarSeverity}
          />
        </div>
      </div>
    </div>
  )
}

export default React.memo(MoreCast2Page)
