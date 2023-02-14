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
import FireCenterDropdown from 'components/FireCenterDropdown'
import WPSDatePicker from 'components/WPSDatePicker'
import { MORE_CAST_2_DOC_TITLE, MORE_CAST_2_NAME } from 'utils/constants'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { WeatherModel, WeatherModelEnum, WeatherModels } from 'features/moreCast2/constants'

const useStyles = makeStyles(theme => ({
  content: {
    display: 'flex',
    flexGrow: 1,
    borderTop: '1px solid black'
  },
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh'
  },
  sidePanel: {
    display: 'flex',
    width: '375px',
    borderRight: '1px solid black'
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
      return fireCenters.find(center => center.id.toString() == id)
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

  return (
    <div className={classes.root} data-testid="more-cast-2-page">
      <GeneralHeader padding="3em" spacing={0.985} title={MORE_CAST_2_NAME} productName={MORE_CAST_2_NAME} />
      <Grid container spacing={1}>
        <Grid item xs={2}>
          <FormControl className={classes.formControl}>
            <FireCenterDropdown
              fireCenterOptions={fireCenters}
              selectedFireCenter={fireCenter}
              setSelectedFireCenter={setFireCenter}
            />
          </FormControl>
        </Grid>
        <Grid item xs={2}>
          <FormControl className={classes.formControl}>
            <WeatherModelDropdown
              weatherModelOptions={WeatherModels}
              selectedWeatherModel={defaultWeatherModel}
              setSelectedWeatherModel={setDefaultWeatherModel}
            />
          </FormControl>
        </Grid>
        <Grid item xs={2}>
          <FormControl className={classes.formControl}>
            <WPSDatePicker date={fromDate} label="From" updateDate={setFromDate} />
          </FormControl>
        </Grid>
        <Grid item xs={2}>
          <FormControl className={classes.formControl}>
            <WPSDatePicker date={toDate} label="To" updateDate={setToDate} />
          </FormControl>
        </Grid>
      </Grid>
      <div className={classes.content}>
        <div className={classes.sidePanel}>
          <StationPanel
            fireCenter={fireCenter}
            selectedStations={selectedStations}
            setSelectedStations={setSelectedStations}
          />
        </div>
      </div>
    </div>
  )
}

export default React.memo(MoreCast2Page)
