import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { FormControl, Grid, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull, isUndefined } from 'lodash'
import { DateTime, Interval } from 'luxon'
import { FireCenter, FireCenterStation } from 'api/fbaAPI'
import { ModelChoice, ModelChoices, ModelType, StationPrediction } from 'api/moreCast2API'
import { selectFireCenters, selectModelStationPredictions } from 'app/rootReducer'
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
import { parseModelsForStationsHelper } from 'features/moreCast2/parseModelsForStationsHelper'

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
    dispatch(getModelStationPredictions(stationCodes, modelType, fromDate.toISODate(), toDate.toISODate()))
  }

  const createEmptyStationPrediction = (code: number, datetime: string, name: string): StationPrediction => {
    const prediction = {
      bias_adjusted_relative_humidity: NaN,
      bias_adjusted_temperature: NaN,
      datetime: datetime,
      precip_24hours: NaN,
      id: window.crypto.randomUUID(),
      model: modelType,
      relative_humidity: NaN,
      station: {
        code,
        name,
        lat: NaN,
        long: NaN,
        ecodivision_name: null,
        core_season: {
          start_month: NaN,
          start_day: NaN,
          end_month: NaN,
          end_day: NaN
        }
      },
      temperature: NaN,
      wind_direction: NaN,
      wind_speed: NaN
    }

    return prediction
  }

  const fillInTheBlanks = () => {
    const missingPredictions: StationPrediction[] = []
    // Iterate through all the station codes and the expected date strings to ensure there is an
    // item in the array for each unique combination
    fireCenter?.stations.forEach(station => {
      dateInterval.forEach(date => {
        const filteredPrediction = stationPredictions.filter(
          p => p.station.code === station.code && p.datetime === date
        )
        if (!filteredPrediction.length) {
          missingPredictions.push(createEmptyStationPrediction(station.code, date, station.name))
        }
      })
    })
    // Use .slice() to create a shallow copy of the predictions from the API and add the missing predictions
    const completeStationPredictions: StationPrediction[] = [...missingPredictions, ...stationPredictions.slice()]
    return completeStationPredictions
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
    // Create an array of UTC datetime strings inclusive of the user selected from/to dates
    // This range of UTC datetimes is needed to help determine when a station is missing a
    // row of predictions
    const interval = Interval.fromDateTimes(fromDate, toDate.plus({ days: 1 }))
    const dateTimeArray = interval.splitBy({ day: 1 }).map(d => d.start)
    const dates = dateTimeArray.map(date => {
      return `${date.toISODate()}T20:00:00+00:00`
    })
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
    const predictions = fillInTheBlanks()
    const newRows = parseModelsForStationsHelper(predictions)
    setStationPredictionsAsMoreCast2ForecastRows(newRows)
  }, [stationPredictions]) // eslint-disable-line react-hooks/exhaustive-deps

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
          <MoreCast2DataGrid rows={forecastRows} setForecastRows={setForecastRows} />
        </div>
      </div>
    </div>
  )
}

export default React.memo(MoreCast2Page)
