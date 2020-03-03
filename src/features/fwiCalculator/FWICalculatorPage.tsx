import React, { useEffect, useState } from 'react'
import { useDispatch } from 'react-redux'

import { Station } from 'api/stationAPI'
import { PageTitle } from 'components/PageTitle'
import { Container } from 'components/Container'
import { fetchStations } from 'features/fwiCalculator/slices/stationsSlice'
import { WeatherStationsDropdown } from 'features/fwiCalculator/components/StationsDropdown'
import { PercentileTextfield } from 'features/fwiCalculator/components/PercentileTextfield'
import {
  fetchPercentiles,
  resetPercentilesResult
} from 'features/fwiCalculator/slices/percentilesSlice'
import { PercentileActionButtons } from 'features/fwiCalculator/components/PercentileActionButtons'
import { FWICalculatorResults } from 'features/fwiCalculator/FWICalculatorResults'
import { TimeRangeSlider } from './components/TimeRangeSlider'

const defaultTimeRange = 10

export const FWICalculatorPage = () => {
  const dispatch = useDispatch()

  const [stations, setStations] = useState<Station[]>([])
  const [timeRange, setTimeRange] = useState<number>(defaultTimeRange)

  useEffect(() => {
    dispatch(fetchStations())
  }, [dispatch])

  const onStationsChange = (s: Station[]) => {
    if (s.length > 3) {
      return
    }
    setStations(s)
  }

  const onYearRangeChange = (timeRange: number) => {
    setTimeRange(timeRange)
  }

  const onCalculateClick = () => {
    const stationCodes = stations.map(s => s.code)
    const percentile = 90
    const currYear = new Date().getFullYear()
    const yearRange = {
      start: currYear - timeRange,
      end: currYear - 1
    }

    dispatch(fetchPercentiles(stationCodes, percentile, yearRange))
  }

  const onResetClick = () => {
    setStations([])
    dispatch(resetPercentilesResult())
    setTimeRange(defaultTimeRange)
  }

  return (
    <>
      <PageTitle title="FWI Calculator" />
      <Container>
        <WeatherStationsDropdown
          stations={stations}
          onStationsChange={onStationsChange}
        />

        <TimeRangeSlider
          timeRange={timeRange}
          onYearRangeChange={onYearRangeChange}
        />

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
