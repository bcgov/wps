import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AlertColor, FormControl, Grid, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isEmpty, isEqual, isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
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
  selectModelStationPredictions,
  selectMoreCast2Forecasts,
  selectStationGroups,
  selectStationGroupsMembers,
  selectObservedDailies
} from 'app/rootReducer'
import { AppDispatch } from 'app/store'
import { GeneralHeader } from 'components'
import { MORE_CAST_2_DOC_TITLE, MORE_CAST_2_NAME } from 'utils/constants'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { getModelStationPredictions } from 'features/moreCast2/slices/modelSlice'
import {
  createDateInterval,
  excludeRowsByModelType,
  fillInTheModelBlanks,
  includeRowsByModelType,
  parseForecastsHelper,
  parseModelsForStationsHelper,
  parseObservedDailiesForStationsHelper,
  replaceColumnValuesFromPrediction
} from 'features/moreCast2/util'
import {
  fillInTheYesterdayDailyBlanks,
  parseYesterdayDailiesForStationsHelper,
  replaceColumnValuesFromYesterdayDaily
} from 'features/moreCast2/yesterdayDailies'
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
import { fetchStationGroups } from 'commonSlices/stationGroupsSlice'
import { StationGroup } from 'api/stationAPI'
import { fetchStationGroupsMembers } from 'commonSlices/selectedStationGroupMembers'
import { getWeatherIndeterminates } from 'features/moreCast2/slices/dataSlice'
import TabbedDataGrid from 'features/moreCast2/components/TabbedDataGrid'
import { selectedStationsChanged, selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'

const useStyles = makeStyles(theme => ({
  content: {
    display: 'flex',
    flexGrow: 1,
    maxHeight: 'calc(100vh - 71.5px)',
    borderTop: '1px solid black',
    overflow: 'hidden'
  },
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  observations: {
    display: 'flex',
    flexDirection: 'column',
    flexGrow: 1,
    overflowX: 'auto'
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    overflow: 'hidden'
  },
  sidePanel: {
    borderRight: '1px solid black',
    display: 'flex',
    minWidth: '375px',
    overflowX: 'hidden',
    overflowY: 'auto',
    width: '375px'
  },
  actionButtonContainer: {
    marginTop: 15
  }
}))

const DEFAULT_MODEL_TYPE_KEY = 'defaultModelType'

const FORECAST_ERROR_MESSAGE = 'The forecast was not saved; an unexpected error occurred.'
const FORECAST_SAVED_MESSAGE = 'Forecast was successfully saved.'
const FORECAST_WARN_MESSAGE = 'A forecast cannot contain N/A values.'

const MoreCast2Page = () => {
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()
  const { groups, loading: groupsLoading } = useSelector(selectStationGroups)
  const { members } = useSelector(selectStationGroupsMembers)
  const { stationPredictions } = useSelector(selectModelStationPredictions)
  const { observedDailies, yesterdayDailies } = useSelector(selectObservedDailies)
  const { moreCast2Forecasts } = useSelector(selectMoreCast2Forecasts)
  const { roles, isAuthenticated } = useSelector(selectAuthentication)
  const { idir } = useSelector(selectAuthentication)

  const [selectedStationGroup, setSelectedStationGroup] = useState<StationGroup>()

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
  const endDateTime = startDateTime.plus({ days: 4 })
  const [fromTo, setFromTo] = useState<DateRange>({
    startDate: startDateTime.toJSDate(),
    endDate: endDateTime.toJSDate()
  })
  const [selectedGroupsMembers, setSelectedGroupsMembers] = useState([...members])
  const [forecastRows, setForecastRows] = useState<MoreCast2ForecastRow[]>([])
  const [modelChoiceAsMoreCast2ForecastRows, setModelChoiceAsMoreCast2ForecastRows] = useState<MoreCast2ForecastRow[]>(
    []
  )
  const [observedRows, setObservedRows] = useState<MoreCast2ForecastRow[]>([])
  const [rowsToDisplay, setRowsToDisplay] = useState<MoreCast2ForecastRow[]>([])
  const [forecastAction, setForecastAction] = useState<ForecastActionType>(ForecastActionChoices[0])
  const [forecastIsDirty, setForecastIsDirty] = useState(false)
  const [forecastsAsMoreCast2ForecastRows, setForecastsAsMoreCast2ForecastRows] = useState<MoreCast2ForecastRow[]>([])
  const [dateInterval, setDateInterval] = useState<string[]>([])

  const { colPrediction } = useSelector(selectColumnModelStationPredictions)
  const { colYesterdayDailies } = useSelector(selectColumnYesterdayDailies)
  const selectedStations = useSelector(selectSelectedStations)

  // const [clickedColDef, setClickedColDef] = React.useState<GridColDef | null>(null)
  // const updateColumnWithModel = (modelType: ModelType, colDef: GridColDef) => {
  //   if (modelType == ModelChoice.YESTERDAY) {
  //     dispatch(
  //       getColumnYesterdayDailies(
  //         modelChoiceAsMoreCast2ForecastRows.map(s => s.stationCode),
  //         selectedStations,
  //         dateInterval,
  //         modelType,
  //         colDef.field as keyof MoreCast2ForecastRow,
  //         DateTime.fromJSDate(fromTo.startDate ? fromTo.startDate : new Date()).toISODate(),
  //         DateTime.fromJSDate(fromTo.endDate ? fromTo.endDate : new Date()).toISODate()
  //       )
  //     )
  //   } else {
  //     dispatch(
  //       getColumnModelStationPredictions(
  //         modelChoiceAsMoreCast2ForecastRows.map(s => s.stationCode),
  //         modelType,
  //         colDef.field as keyof MoreCast2ForecastRow,
  //         DateTime.fromJSDate(fromTo.startDate ? fromTo.startDate : new Date()).toISODate(),
  //         DateTime.fromJSDate(fromTo.endDate ? fromTo.endDate : new Date()).toISODate()
  //       )
  //     )
  //   }
  // }

  const fetchWeatherIndeterminates = () => {
    if (fromTo && fromTo.startDate && fromTo.endDate) {
      dispatch(
        getWeatherIndeterminates(
          members.map(station => station.station_code),
          DateTime.fromJSDate(fromTo.startDate),
          DateTime.fromJSDate(fromTo.endDate)
        )
      )
    }
  }

  // Fetches observed/predicted values while in Create Forecast mode
  const fetchStationPredictions = () => {
    const stationCodes = members.map(member => member.station_code)
    if (isUndefined(fromTo.startDate) || isUndefined(fromTo.endDate)) {
      setForecastRows([])
      return
    }
    if (!isEqual(modelType, ModelChoice.YESTERDAY)) {
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
    const stationCodes = members.map(member => member.station_code) || []
    if (!isUndefined(fromTo.startDate) && !isUndefined(fromTo.endDate)) {
      if (isEqual(modelType, ModelChoice.YESTERDAY) && fromTo.startDate.toISOString() >= DateTime.now().toISODate()) {
        // if using Yesterday model type but fromTo date interval doesn't include a date for which observations will be
        // available, need to modify the requested for ObservedStationDailies to get the most recent observation, which
        // will be applied as Yesterday values for the relevant dates.
        const modifiedStartDate = currentTimeIsBeforeNoon
          ? DateTime.now().minus({ days: 1 }).toISODate()
          : DateTime.now().toISODate()
        dispatch(
          getObservedStationDailies(stationCodes, modifiedStartDate, DateTime.fromJSDate(fromTo.endDate).toISODate())
        )
      } else {
        dispatch(
          getObservedStationDailies(
            stationCodes,
            DateTime.fromJSDate(fromTo.startDate).toISODate(),
            DateTime.fromJSDate(fromTo.endDate).toISODate()
          )
        )
      }
    }
  }

  // Fetches previously submitted forecasts from the API database while in View/Edit Forecast mode
  const fetchForecasts = () => {
    const stationCodes = selectedGroupsMembers.map(member => member.station_code)
    if (isUndefined(fromTo.startDate) || isUndefined(fromTo.endDate)) {
      setForecastRows([])
      return
    }
    dispatch(
      getMoreCast2Forecasts(DateTime.fromJSDate(fromTo.startDate), DateTime.fromJSDate(fromTo.endDate), stationCodes)
    )
  }

  useEffect(() => {
    document.title = MORE_CAST_2_DOC_TITLE
    dispatch(fetchStationGroups())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isNull(colPrediction)) {
      const newRows = replaceColumnValuesFromPrediction(
        modelChoiceAsMoreCast2ForecastRows,
        selectedStations,
        dateInterval,
        colPrediction
      )
      setModelChoiceAsMoreCast2ForecastRows(newRows)
    }
  }, [colPrediction]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isNull(colYesterdayDailies)) {
      const newRows = replaceColumnValuesFromYesterdayDaily(
        modelChoiceAsMoreCast2ForecastRows,
        selectedStations,
        dateInterval,
        colYesterdayDailies
      )
      setModelChoiceAsMoreCast2ForecastRows(newRows)
    }
  }, [colYesterdayDailies]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isEmpty(members)) {
      dispatch(selectedStationsChanged([members[0]]))
      setSelectedGroupsMembers(members)
      fetchStationPredictions()
      fetchStationObservedDailies()
    }
    fetchWeatherIndeterminates()
  }, [members]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isUndefined(modelType) && !isNull(modelType)) {
      localStorage.setItem(DEFAULT_MODEL_TYPE_KEY, modelType)
      fetchStationPredictions()
      fetchStationObservedDailies()
    } else {
      setForecastRows([])
    }
  }, [modelType]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isEmpty(selectedStationGroup)) {
      dispatch(fetchStationGroupsMembers([selectedStationGroup.id]))
    } else {
      setSelectedGroupsMembers([])
      setForecastRows([])
      setObservedRows([])
      setRowsToDisplay([])
      setForecastsAsMoreCast2ForecastRows([])
      setModelChoiceAsMoreCast2ForecastRows([])
    }
  }, [selectedStationGroup]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isUndefined(fromTo.startDate) && !isUndefined(fromTo.endDate)) {
      const dates = createDateInterval(DateTime.fromJSDate(fromTo.startDate), DateTime.fromJSDate(fromTo.endDate))
      setDateInterval(dates)
    }

    if (forecastAction === ForecastActionChoice.CREATE) {
      if (!isUndefined(modelType) && !isNull(modelType)) {
        localStorage.setItem(DEFAULT_MODEL_TYPE_KEY, modelType)
        fetchWeatherIndeterminates()
      } else {
        setForecastRows([])
      }
    } else {
      // We're in view/edit mode
      fetchForecasts()
    }
  }, [fromTo.startDate, fromTo.endDate]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const predictions = fillInTheModelBlanks(selectedGroupsMembers, stationPredictions, dateInterval, modelType)
    const newRows = parseModelsForStationsHelper(predictions)
    setModelChoiceAsMoreCast2ForecastRows(newRows)
  }, [stationPredictions]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (modelType === ModelChoice.YESTERDAY) {
      const completeDailies = fillInTheYesterdayDailyBlanks(selectedGroupsMembers, yesterdayDailies, dateInterval)
      const newRows = parseYesterdayDailiesForStationsHelper(completeDailies)
      setModelChoiceAsMoreCast2ForecastRows(newRows)
    }
  }, [yesterdayDailies]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const newRows = parseObservedDailiesForStationsHelper(observedDailies)
    setObservedRows(newRows)
  }, [observedDailies]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Handle the switch from create to edit mode and vice versa
    if (forecastAction === ForecastActionChoice.CREATE) {
      fetchStationPredictions()
      fetchStationObservedDailies()
    } else fetchForecasts()
  }, [forecastAction]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const newRows = parseForecastsHelper(moreCast2Forecasts, selectedGroupsMembers)
    setForecastsAsMoreCast2ForecastRows(newRows)
    if (forecastAction === ForecastActionChoice.EDIT) {
      setRowsToDisplay(newRows)
    }
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
        ? excludeRowsByModelType(rowsToDisplay, ModelChoice.ACTUAL)
        : includeRowsByModelType(rowsToDisplay, ModelChoice.MANUAL)

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

  // Checks if the displayed rows includes non-Actual rows
  const hasForecastRow = () => {
    for (const row of rowsToDisplay) {
      if (row.precip.choice !== ModelChoice.ACTUAL) {
        return true
      }
    }
    return false
  }

  return (
    <div className={classes.root} data-testid="more-cast-2-page">
      <GeneralHeader padding="3em" spacing={0.985} title={MORE_CAST_2_NAME} productName={MORE_CAST_2_NAME} />
      <div className={classes.content}>
        <div className={classes.sidePanel}>
          <StationPanel
            idir={idir}
            loading={groupsLoading}
            stationGroups={groups}
            selectedStationGroup={selectedStationGroup}
            setSelectedStationGroup={setSelectedStationGroup}
            stationGroupMembers={selectedGroupsMembers}
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
                    hasForecastRow() &&
                    (forecastAction === ForecastActionChoice.CREATE || forecastIsDirty)
                  }
                  label={forecastAction === ForecastActionChoice.CREATE ? 'Save Forecast' : 'Update Forecast'}
                  onClick={handleSaveClick}
                />
              </FormControl>
            </Grid>
          </Grid>
          <TabbedDataGrid onCellEditStop={setForecastIsDirty} />
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
