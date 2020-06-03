import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { makeStyles } from '@material-ui/core/styles'

import { Station } from 'api/stationAPI'
import { selectAuthentication } from 'app/rootReducer'
import { PageHeader, PageTitle, Container } from 'components'
import WxStationDropdown from 'features/stations/components/WxStationDropdown'
import WxDisplaysByStations from 'features/fireWeather/components/WxDataDisplays'
import {
  authenticate,
  setAxiosRequestInterceptors
} from 'features/auth/slices/authenticationSlice'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { fetchModels } from 'features/fireWeather/slices/modelsSlice'
import { fetchReadings } from 'features/fireWeather/slices/readingsSlice'
import GetWxDataButton from '../components/GetWxDataButton'

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
    setRequestedStations(selectedStations)
    const stationCodes = selectedStations.map(s => s.code)
    dispatch(fetchModels(stationCodes))
    dispatch(fetchReadings(stationCodes))
  }

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
        <GetWxDataButton onBtnClick={onSubmitClick} selectedStations={selectedStations} />
        <WxDisplaysByStations requestedStations={requestedStations} />
      </Container>
    </div>
  )
}

export default React.memo(FireWeatherPage)
