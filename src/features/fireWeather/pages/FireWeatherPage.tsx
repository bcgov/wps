import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { makeStyles } from '@material-ui/core/styles'

import { Station } from 'api/stationAPI'
import { selectAuthentication, selectModels, selectReadings } from 'app/rootReducer'
import { PageHeader, PageTitle, Container, Button } from 'components'
import WxStationDropdown from 'features/stations/components/WxStationDropdown'
import WxDisplaysByStations from 'features/fireWeather/components/WxDisplaysByStations'
import {
  authenticate,
  setAxiosRequestInterceptors
} from 'features/auth/slices/authenticationSlice'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { fetchModels } from 'features/fireWeather/slices/modelsSlice'
import { fetchReadings } from 'features/fireWeather/slices/readingsSlice'

const useStyles = makeStyles({
  stationDropdown: {
    marginBottom: 10
  }
})

// TODO: Separate authentication part from this later
const FireWeatherPage = () => {
  const classes = useStyles()
  const dispatch = useDispatch()
  const [selectedStations, setStations] = useState<Station[]>([])
  const [requestedStations, setRequestedStations] = useState<Station[]>([])
  const { isAuthenticated, authenticating, error } = useSelector(selectAuthentication)
  const { loading: loadingModels } = useSelector(selectModels)
  const { loading: loadingReadings } = useSelector(selectReadings)

  useEffect(() => {
    dispatch(authenticate())
    dispatch(setAxiosRequestInterceptors())
    dispatch(fetchWxStations())
  }, [dispatch])

  if (error) {
    return <div>{error}</div>
  }

  if (authenticating) {
    return <div>Signing in...</div>
  }

  if (!isAuthenticated) {
    return <div>You are not authenticated!</div>
  }

  const onStationsChange = (s: Station[]) => {
    setStations(s)
  }
  const onSubmitClick = () => {
    const stationCodes = selectedStations.map(s => s.code)
    setRequestedStations(selectedStations)
    dispatch(fetchModels(stationCodes))
    dispatch(fetchReadings(stationCodes))
  }

  const wxDataLoading = loadingModels || loadingReadings
  const isBtnDisabled = selectedStations.length === 0

  return (
    <div data-testid="fire-weather-page">
      <PageHeader title="Predictive Services Unit" />
      <PageTitle title="Daily Weather Model" />
      <Container>
        <WxStationDropdown
          className={classes.stationDropdown}
          stations={selectedStations}
          onStationsChange={onStationsChange}
        />
        <Button
          data-testid="get-wx-data-button"
          onClick={onSubmitClick}
          disabled={isBtnDisabled}
          loading={wxDataLoading}
          variant="contained"
          color="primary"
        >
          Get Historic Readings &amp; Global Model Data
        </Button>
        <WxDisplaysByStations stations={requestedStations} />
      </Container>
    </div>
  )
}

export default React.memo(FireWeatherPage)
