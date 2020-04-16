import React, { useEffect, useState } from 'react'
import { useDispatch } from 'react-redux'

import { Station } from 'api/stationAPI'
import { PageHeader } from 'components/PageHeader'
import { PageTitle } from 'components/PageTitle'
import { Container } from 'components/Container'
import { fetchStations } from 'features/percentileCalculator/slices/stationsSlice'
import { WeatherStationsDropdown } from 'features/percentileCalculator/components/StationsDropdown'
import { PercentileTextfield } from 'features/percentileCalculator/components/PercentileTextfield'
import {
  fetchPercentiles,
  resetPercentilesResult
} from 'features/percentileCalculator/slices/percentilesSlice'
import { PercentileActionButtons } from 'features/percentileCalculator/components/PercentileActionButtons'
import { PercentileResults } from 'features/percentileCalculator/components/PercentileResults'
import { TimeRangeSlider } from '../components/TimeRangeSlider'

const defaultTimeRange = 10
const defaultPercentile = 90

export const PercentileCalculatorPage = () => {
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
    const currYear = new Date().getFullYear()
    const yearRange = {
      start: currYear - timeRange,
      end: currYear - 1
    }

    dispatch(fetchPercentiles(stationCodes, defaultPercentile, yearRange))
  }

  const onResetClick = () => {
    setStations([])
    dispatch(resetPercentilesResult())
    setTimeRange(defaultTimeRange)
  }

  return (
    <div data-testid="percentile-calculator-page">
      <PageHeader title="Predictive Services Unit" />
      <PageTitle title="Percentile Calculator" />
      <Container>
        <WeatherStationsDropdown
          stations={stations}
          onStationsChange={onStationsChange}
        />

        <TimeRangeSlider timeRange={timeRange} onYearRangeChange={onYearRangeChange} />

        <PercentileTextfield />

        <PercentileActionButtons
          stations={stations}
          onCalculateClick={onCalculateClick}
          onResetClick={onResetClick}
        />

        <PercentileResults />
      </Container>
    </div>
  )
}
