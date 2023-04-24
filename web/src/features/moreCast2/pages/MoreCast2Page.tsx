import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AlertColor } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isEmpty, isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import {
  DEFAULT_MODEL_TYPE,
  ForecastActionChoices,
  ForecastActionType,
  ModelType,
  submitMoreCastForecastRecords
} from 'api/moreCast2API'
import { selectAuthentication, selectStationGroups, selectStationGroupsMembers } from 'app/rootReducer'
import { AppDispatch } from 'app/store'
import { GeneralHeader } from 'components'
import { MORE_CAST_2_DOC_TITLE, MORE_CAST_2_NAME } from 'utils/constants'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { DateRange } from 'components/dateRangePicker/types'
import MoreCast2Snackbar from 'features/moreCast2/components/MoreCast2Snackbar'
import { fetchStationGroups } from 'commonSlices/stationGroupsSlice'
import { StationGroup } from 'api/stationAPI'
import { fetchStationGroupsMembers } from 'commonSlices/selectedStationGroupMembers'
import { getWeatherIndeterminates, selectAllMoreCast2Rows } from 'features/moreCast2/slices/dataSlice'
import TabbedDataGrid from 'features/moreCast2/components/TabbedDataGrid'
import { selectedStationsChanged } from 'features/moreCast2/slices/selectedStationsSlice'

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
  const { idir } = useSelector(selectAuthentication)
  // All MoreCast2Rows derived from WeatherIndeterminates in dataSlice.ts. Updates in response to
  // a change of station group or date range.
  const sortedMoreCast2Rows = useSelector(selectAllMoreCast2Rows)

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
  const [forecastAction, setForecastAction] = useState<ForecastActionType>(ForecastActionChoices[0])

  const fetchWeatherIndeterminates = () => {
    if (fromTo && fromTo.startDate && fromTo.endDate) {
      dispatch(
        getWeatherIndeterminates(members, DateTime.fromJSDate(fromTo.startDate), DateTime.fromJSDate(fromTo.endDate))
      )
    }
  }

  useEffect(() => {
    document.title = MORE_CAST_2_DOC_TITLE
    dispatch(fetchStationGroups())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isEmpty(members)) {
      dispatch(selectedStationsChanged([members[0]]))
      setSelectedGroupsMembers(members)
    }
    fetchWeatherIndeterminates()
  }, [members]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isEmpty(selectedStationGroup)) {
      dispatch(fetchStationGroupsMembers([selectedStationGroup.id]))
    } else {
      setSelectedGroupsMembers([])
    }
  }, [selectedStationGroup]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isUndefined(modelType) && !isNull(modelType)) {
      localStorage.setItem(DEFAULT_MODEL_TYPE_KEY, modelType)
      fetchWeatherIndeterminates()
    }
  }, [fromTo.startDate, fromTo.endDate]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSaveClick = async () => {
    const rowsToSave: MoreCast2ForecastRow[] = sortedMoreCast2Rows.flatMap(row => {
      if (
        isUndefined(row.precipForecast) ||
        isUndefined(row.rhForecast) ||
        isUndefined(row.tempForecast) ||
        isUndefined(row.windDirectionForecast) ||
        isUndefined(row.windSpeedForecast)
      ) {
        return []
      }
      return {
        id: row.id,
        stationCode: row.stationCode,
        stationName: row.stationName,
        forDate: row.forDate,
        precip: row.precipForecast,
        rh: row.rhForecast,
        temp: row.tempForecast,
        windDirection: row.windDirectionForecast,
        windSpeed: row.windSpeedForecast
      }
    })

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
    for (const row of sortedMoreCast2Rows) {
      if (
        !isUndefined(row.precipForecast) &&
        !isUndefined(row.rhForecast) &&
        !isUndefined(row.tempForecast) &&
        !isUndefined(row.windSpeedForecast)
      ) {
        return true
      }
    }
    return false
  }

  // A valid, submittable forecast can't contain NaN for any values
  const forecastIsValid = () => {
    // for (const row of sortedMoreCast2Rows) {
    //   if (
    //     (row.precipForecast && isNaN(row.precipForecast.value)) ||
    //     (row.rhForecast && isNaN(row.rhForecast.value)) ||
    //     (row.tempForecast && isNaN(row.tempForecast.value)) ||
    //     (row.windSpeedForecast && isNaN(row.windSpeedForecast.value))
    //   ) {
    //     return false
    //   }
    // }
    return true
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
          <TabbedDataGrid
            forecastAction={forecastAction}
            setForecastAction={setForecastAction}
            morecast2Rows={sortedMoreCast2Rows}
            fetchWeatherIndeterminates={fetchWeatherIndeterminates}
            fromTo={fromTo}
            setFromTo={setFromTo}
            modelType={modelType}
            setModelType={setModelType}
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
