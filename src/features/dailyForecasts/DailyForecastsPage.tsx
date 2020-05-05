import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { makeStyles } from '@material-ui/core/styles'

import { Station } from 'api/stationAPI'
import { selectAuthentication, selectForecasts } from 'app/rootReducer'
import { PageHeader, PageTitle, Container, Button } from 'components'
import { authenticate } from 'features/auth/slices/authenticationSlice'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { WxStationDropdown } from 'features/stations/components/WxStationDropdown'
import { fetchForecasts } from 'features/dailyForecasts/slices/ForecastsSlice'
import { DailyForecastsDisplay } from 'features/dailyForecasts/components/DailyForecastsDisplay'

const useStyles = makeStyles({
  stationDropdown: {
    marginBottom: 10
  }
})

export const DailyForecastsPage = () => {
  const dispatch = useDispatch()
  const classes = useStyles()

  const [selectedStations, setStations] = useState<Station[]>([])

  const { isAuthenticated, authenticating, error } = useSelector(selectAuthentication)
  const { loading: wxDataLoading } = useSelector(selectForecasts)

  useEffect(() => {
    dispatch(authenticate())
    dispatch(fetchWxStations())
  }, [dispatch])

  const onStationsChange = (s: Station[]) => {
    setStations(s)
  }
  const onSubmitClick = () => {
    const stationCodes = selectedStations.map(s => s.code)
    dispatch(fetchForecasts(stationCodes))
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
          Get Wx Forecast Data
        </Button>
        <DailyForecastsDisplay />
      </Container>
    </div>
  )
}
