import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { FormControl, Grid, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import { FireCenter, FireCenterStation } from 'api/fbaAPI'
import { ModelChoice, ModelChoices, ModelType } from 'api/moreCast2API'
import { selectFireCenters, selectModelStationPredictions, selectYesterdayDailies } from 'app/rootReducer'
import { AppDispatch } from 'app/store'
import { fetchFireCenters } from 'commonSlices/fireCentersSlice'
import { GeneralHeader } from 'components'
import WPSDatePicker from 'components/WPSDatePicker'
import { MORE_CAST_2_DOC_TITLE, MORE_CAST_2_NAME } from 'utils/constants'
import MoreCast2DataGrid from 'features/moreCast2/components/MoreCast2DataGrid'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { getModelStationPredictions } from 'features/moreCast2/slices/modelSlice'
import { createDateInterval, fillInTheModelBlanks, parseModelsForStationsHelper } from 'features/moreCast2/util'
import {
  fillInTheYesterdayDailyBlanks,
  parseYesterdayDailiesForStationsHelper
} from 'features/moreCast2/yesterdayDailies'
import { getYesterdayStationDailies } from 'features/moreCast2/slices/yesterdayDailiesSlice'

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
  }
}))

const DEFAULT_MODEL_TYPE_KEY = 'defaultModelType'
const DEFAULT_FIRE_CENTER_KEY = 'preferredMoreCast2FireCenter'
const DEFAULT_MODEL_TYPE: ModelType = ModelChoice.HRDPS

const MoreCast2Page = () => {
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()
  const { fireCenters } = useSelector(selectFireCenters)
  const { stationPredictions } = useSelector(selectModelStationPredictions)
  const { yesterdayDailies } = useSelector(selectYesterdayDailies)
  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)
  const [selectedStations, setSelectedStations] = useState<FireCenterStation[]>([])
  const [modelType, setModelType] = useState<ModelType>(
    (localStorage.getItem(DEFAULT_MODEL_TYPE_KEY) as ModelType) || DEFAULT_MODEL_TYPE
  )
  const [fromDate, setFromDate] = useState<DateTime>(DateTime.now())
  const [toDate, setToDate] = useState<DateTime>(DateTime.now().plus({ days: 2 }))
  const [forecastRows, setForecastRows] = useState<MoreCast2ForecastRow[]>([])
  const [stationPredictionsAsMoreCast2ForecastRows, setStationPredictionsAsMoreCast2ForecastRows] = useState<
    MoreCast2ForecastRow[]
  >([])
  const [dateInterval, setDateInterval] = useState<string[]>([])

  const fetchStationPredictions = () => {
    const stationCodes = fireCenter?.stations.map(station => station.code) || []
    if (toDate <= fromDate) {
      setForecastRows([])
      return
    }
    if (modelType == ModelChoice.YESTERDAY) {
      dispatch(getYesterdayStationDailies(stationCodes, fromDate.toISODate()))
    } else {
      dispatch(getModelStationPredictions(stationCodes, modelType, fromDate.toISODate(), toDate.toISODate()))
    }
  }

  useEffect(() => {
    dispatch(fetchFireCenters())
    document.title = MORE_CAST_2_DOC_TITLE
    fetchStationPredictions()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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

    setSelectedStations(fireCenter?.stations || [])
    fetchStationPredictions()
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
    const dates = createDateInterval(fromDate, toDate)
    setDateInterval(dates)

    if (!isUndefined(modelType) && !isNull(modelType)) {
      localStorage.setItem(DEFAULT_MODEL_TYPE_KEY, modelType)
      fetchStationPredictions()
    } else {
      setForecastRows([])
    }
  }, [fromDate, toDate]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const visibleForecastRows = stationPredictionsAsMoreCast2ForecastRows.filter(
      row => selectedStations.filter(station => station.code === row.stationCode).length
    )
    setForecastRows(visibleForecastRows)
  }, [stationPredictionsAsMoreCast2ForecastRows, selectedStations])

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
          <Typography variant="h5">Observations</Typography>
          <Grid container spacing={1}>
            <Grid item xs={3}>
              <FormControl className={classes.formControl}>
                <WeatherModelDropdown
                  weatherModelOptions={ModelChoices}
                  selectedModelType={modelType}
                  setSelectedModelType={setModelType}
                />
              </FormControl>
            </Grid>
            <Grid item xs={3}>
              <FormControl className={classes.formControl}>
                <WPSDatePicker date={fromDate} label="From" updateDate={setFromDate} />
              </FormControl>
            </Grid>
            <Grid item xs={3}>
              <FormControl className={classes.formControl}>
                <WPSDatePicker date={toDate} label="To" updateDate={setToDate} />
              </FormControl>
            </Grid>
          </Grid>
          <MoreCast2DataGrid rows={forecastRows} />
        </div>
      </div>
    </div>
  )
}

export default React.memo(MoreCast2Page)
