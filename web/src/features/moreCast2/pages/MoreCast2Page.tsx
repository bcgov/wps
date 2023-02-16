import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { FormControl, Grid, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import { FireCenter, FireCenterStation } from 'api/fbaAPI'
import { selectFireCenters } from 'app/rootReducer'
import { AppDispatch } from 'app/store'
import { fetchFireCenters } from 'commonSlices/fireCentersSlice'
import { GeneralHeader } from 'components'
import WPSDatePicker from 'components/WPSDatePicker'
import { MORE_CAST_2_DOC_TITLE, MORE_CAST_2_NAME } from 'utils/constants'
import NextCastDataGrid from 'features/moreCast2/components/NextCastDataGrid'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { WeatherModel, WeatherModelEnum, WeatherModels } from 'features/moreCast2/constants'
import { ForecastRow } from 'features/moreCast2/components/NextCastDataGrid'

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

const DEFAULT_WEATHER_MODEL_KEY = 'defaultWeatherModel'
const PREFERRED_FIRE_CENTER_KEY = 'preferredMoreCast2FireCenter'

const MoreCast2Page = () => {
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()
  const { fireCenters } = useSelector(selectFireCenters)
  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)
  const [selectedStations, setSelectedStations] = useState<FireCenterStation[]>([])
  const [defaultWeatherModel, setDefaultWeatherModel] = useState<WeatherModel | undefined>(undefined)
  const [fromDate, setFromDate] = useState<DateTime>(DateTime.now())
  const [toDate, setToDate] = useState<DateTime>(DateTime.now().plus({ days: 3 }))

  useEffect(() => {
    dispatch(fetchFireCenters())
    document.title = MORE_CAST_2_DOC_TITLE

    const findDefaultWeatherModel = (name: string) => {
      return WeatherModels.find(model => model.name === name)
    }

    const model = localStorage.getItem(DEFAULT_WEATHER_MODEL_KEY) || WeatherModelEnum.HRDPS
    setDefaultWeatherModel(findDefaultWeatherModel(model))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const findCenter = (id: string | null): FireCenter | undefined => {
      return fireCenters.find((center: FireCenter) => center.id.toString() == id)
    }
    if (fireCenters.length) {
      setFireCenter(findCenter(localStorage.getItem(PREFERRED_FIRE_CENTER_KEY)))
    }
  }, [fireCenters])

  useEffect(() => {
    if (fireCenter?.id) {
      localStorage.setItem(PREFERRED_FIRE_CENTER_KEY, fireCenter?.id.toString())
    }
    if (fireCenter?.stations && fireCenter.stations.length && (isNull(fireCenter) || isUndefined(fireCenter))) {
      localStorage.removeItem(PREFERRED_FIRE_CENTER_KEY)
    }
  }, [fireCenter])

  useEffect(() => {
    if (!isUndefined(defaultWeatherModel)) {
      localStorage.setItem(DEFAULT_WEATHER_MODEL_KEY, defaultWeatherModel.name)
    }
  }, [defaultWeatherModel])

  const sampleRows: ForecastRow[] = [
    { id: 1, station: 'Akton', for_date: 1676318400000, temp: 5, rh: 90, windDirection: 175, windSpeed: 10, precip: 2 },
    { id: 2, station: 'Akton', for_date: 1676404800000, temp: 6, rh: 90, windDirection: 185, windSpeed: 15, precip: 1 },
    { id: 3, station: 'Akton', for_date: 1676491200000, temp: 5, rh: 90, windDirection: 190, windSpeed: 25, precip: 1 },
    {
      id: 4,
      station: 'Ashnola',
      for_date: 1676318400000,
      temp: 3,
      rh: 95,
      windDirection: 160,
      windSpeed: 5,
      precip: 25
    },
    {
      id: 5,
      station: 'Ashnola',
      for_date: 1676404800000,
      temp: 2,
      rh: 95,
      windDirection: 145,
      windSpeed: 10,
      precip: 15
    },
    {
      id: 6,
      station: 'Ashnola',
      for_date: 1676491200000,
      temp: 1,
      rh: 95,
      windDirection: 95,
      windSpeed: 10,
      precip: 20
    },
    {
      id: 7,
      station: 'Cahily',
      for_date: 1676318400000,
      temp: 4,
      rh: 75,
      windDirection: 355,
      windSpeed: 25,
      precip: 0
    },
    { id: 8, station: 'Cahily', for_date: 1676404800000, temp: 4, rh: 75, windDirection: 5, windSpeed: 35, precip: 0 },
    { id: 9, station: 'Cahily', for_date: 1676491200000, temp: 5, rh: 75, windDirection: 10, windSpeed: 45, precip: 5 }
  ]

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
                  weatherModelOptions={WeatherModels}
                  selectedWeatherModel={defaultWeatherModel}
                  setSelectedWeatherModel={setDefaultWeatherModel}
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
          <NextCastDataGrid rows={sampleRows} />
        </div>
      </div>
    </div>
  )
}

export default React.memo(MoreCast2Page)
