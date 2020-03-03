import React, { useEffect, useState } from 'react'
import { useDispatch } from 'react-redux'

import { Station } from 'api/stationAPI'
import { PageTitle } from 'components/PageTitle'
import { Container } from 'components/Container'
import { fetchStations } from 'features/fwiCalculator/slices/stationsSlice'
import {
  fetchPercentiles,
  resetPercentilesResult
} from 'features/fwiCalculator/slices/percentilesSlice'
import { WeatherStationsDropdown } from 'features/fwiCalculator/components/StationsDropdown'
import { PercentileActionButtons } from 'features/fwiCalculator/components/PercentileActionButtons'
import { TimeRangeTextfield } from 'features/fwiCalculator/components/TimeRangeTextfield'
import { PercentileTextfield } from 'features/fwiCalculator/components/PercentileTextfield'
import { FWICalculatorResults } from 'features/fwiCalculator/FWICalculatorResults'

export const FWICalculatorPage = () => {
  const dispatch = useDispatch()
  const [stations, setStations] = useState<Station[]>([])

  useEffect(() => {
    dispatch(fetchStations())
  }, [dispatch])

  const onStationsChange = (s: Station[]) => {
    if (s.length > 3) {
      return
    }
    setStations(s)
  }

  const onCalculateClick = () => {
    const stationCodes = stations.map(s => s.code)
    const percentile = 90
    const yearRange = { start: 2010, end: 2019 }
    dispatch(fetchPercentiles(stationCodes, percentile, yearRange))
  }

  const onResetClick = () => {
    setStations([])
    dispatch(resetPercentilesResult())
  }

  return (
    <>
      <PageTitle title="FWI Calculator" />
      <Container>
        <WeatherStationsDropdown
          stations={stations}
          onStationsChange={onStationsChange}
        />

        <TimeRangeTextfield />

        <PercentileTextfield />

        <PercentileActionButtons
          stations={stations}
          onCalculateClick={onCalculateClick}
          onResetClick={onResetClick}
        />

        <FWICalculatorResults />
      </Container>
    </>
  )
}
