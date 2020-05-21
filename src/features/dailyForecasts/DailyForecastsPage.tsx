import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { makeStyles } from '@material-ui/core/styles'

import { Station } from 'api/stationAPI'
import { selectAuthentication, selectForecasts, selectHourlies } from 'app/rootReducer'
import { PageHeader, PageTitle, Container, Button } from 'components'
import {
  authenticate,
  setAxiosRequestInterceptors
} from 'features/auth/slices/authenticationSlice'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { WxStationDropdown } from 'features/stations/components/WxStationDropdown'
import { fetchForecasts } from 'features/dailyForecasts/slices/ForecastsSlice'
import { fetchHistoricalReadings } from 'features/hourlies/slices/HourliesSlice'
import { DailyForecastsDisplay } from 'features/dailyForecasts/components/DailyForecastsDisplay'
import { HourlyReadingsDisplay } from 'features/hourlies/components/HourlyReadingsDisplay'

const useStyles = makeStyles({
  stationDropdown: {
    marginBottom: 10
  }
})

// TODO: Separate authentication part from this later
export const DailyForecastsPage = () => {
  const dispatch = useDispatch()
  const classes = useStyles()

  const [selectedStations, setStations] = useState<Station[]>([])

  const { isAuthenticated, authenticating, error } = useSelector(selectAuthentication)
  const { loading: forecastDataLoading } = useSelector(selectForecasts)
  const { loading: hourlyDataLoading } = useSelector(selectHourlies)
  const wxDataLoading = forecastDataLoading || hourlyDataLoading

  useEffect(() => {
    dispatch(authenticate())
    dispatch(setAxiosRequestInterceptors())
    dispatch(fetchWxStations())
  }, [dispatch])

  const onStationsChange = (s: Station[]) => {
    setStations(s)
  }
  const onSubmitClick = () => {
    const stationCodes = selectedStations.map(s => s.code)
    dispatch(fetchForecasts(stationCodes))
    dispatch(fetchHistoricalReadings(stationCodes))
  }

  if (error) {
    return <div>{error}</div>
  }

  if (authenticating) {
    return <div>Signing in...</div>
  }

  if (!isAuthenticated) {
    return <div>You are not authenticated!</div>
  }

  const isBtnDisabled = wxDataLoading || selectedStations.length === 0

  return (
    <div data-testid="daily-forecasts-page">
      <PageHeader title="Predictive Services Unit" />
      <PageTitle title="Daily Weather Forecast" />
      <Container>
        <WxStationDropdown
          className={classes.stationDropdown}
          stations={selectedStations}
          onStationsChange={onStationsChange}
        />
        <Button
          data-testid="get-forecast-wx-button"
          onClick={onSubmitClick}
          disabled={isBtnDisabled}
          loading={wxDataLoading}
          variant="contained"
          color="primary"
        >
          Get Historic Readings and Forecasted Global Model Data
        </Button>
        <DailyForecastsDisplay />
        <HourlyReadingsDisplay />
      </Container>
    </div>
  )
}
