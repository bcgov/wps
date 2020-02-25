import React, { useEffect } from 'react'
import { useDispatch } from 'react-redux'

import { fetchStations } from 'features/fwiCalculator/slices/stationsSlice'
import { WeatherStationsDropdown } from './components/StationsDropdown'
import { Station } from 'api/stationAPI'
import { PageTitle } from 'components/PageTitle'
import { Container } from 'components/Container'

export const FWICalculatorPage = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(fetchStations())
  }, [dispatch])

  const onStationChange = (station: Station | null) => {
    // Todo: reflect the station change
  }

  return (
    <>
      <PageTitle title="FWI Calculator" />
      <Container>
        <WeatherStationsDropdown onStationChange={onStationChange} />
      </Container>
    </>
  )
}
