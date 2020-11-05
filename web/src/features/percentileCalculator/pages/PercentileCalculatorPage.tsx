import React, { useEffect, useState } from 'react'
import { useDispatch } from 'react-redux'

import { Station } from 'api/stationAPI'
import { PageHeader, PageTitle, Container, ErrorBoundary } from 'components'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import WxStationDropdown from 'features/stations/components/WxStationDropdown'
import { PercentileTextfield } from 'features/percentileCalculator/components/PercentileTextfield'
import {
  fetchPercentiles,
  resetPercentilesResult
} from 'features/percentileCalculator/slices/percentilesSlice'
import { PercentileActionButtons } from 'features/percentileCalculator/components/PercentileActionButtons'
import { PercentileResults } from 'features/percentileCalculator/components/PercentileResults'
import { TimeRangeSlider } from 'features/percentileCalculator/components/TimeRangeSlider'

const defaultTimeRange = 10
const defaultPercentile = 90

export const PercentileCalculatorPage: React.FunctionComponent = () => {
  const dispatch = useDispatch()

  const [selectedStations, setStations] = useState<Station[]>([])
  const [timeRange, setTimeRange] = useState<number>(defaultTimeRange)

  useEffect(() => {
    dispatch(fetchWxStations())
  }, [dispatch])

  const onCalculateClick = () => {
    const stationCodes = selectedStations.map(s => s.code)
    const currYear = new Date().getFullYear()
    const yearRange = {
      start: currYear - timeRange,
      end: currYear - 1
    }

    dispatch(fetchPercentiles(stationCodes, defaultPercentile, yearRange))

    // Create a matomo event, pushing various variables onto the dataLayer
    // NOTE: This section is proof of concept - strongly consider re-factoring when adding other events.
    // TODO: Re-evaluate this way of implementing Matomo once we know more about it.
    if (window._mtm) {
      // see: https://developer.matomo.org/guides/tagmanager/integration-plugin#supporting-the-data-layer
      window._mtm.push({
        event: 'calculatePercentiles',
        stationCodes: stationCodes,
        percentile: defaultPercentile,
        yearRange: yearRange
      })
    }
  }

  const onResetClick = () => {
    setStations([])
    setTimeRange(defaultTimeRange)
    dispatch(resetPercentilesResult())
  }

  return (
    <main data-testid="percentile-calculator-page">
      <PageHeader title="Predictive Services Unit" />
      <PageTitle title="Percentile Calculator" />
      <Container>
        <WxStationDropdown stations={selectedStations} onStationsChange={setStations} />

        <TimeRangeSlider timeRange={timeRange} onYearRangeChange={setTimeRange} />

        <PercentileTextfield />

        <PercentileActionButtons
          stations={selectedStations}
          onCalculateClick={onCalculateClick}
          onResetClick={onResetClick}
        />

        <ErrorBoundary>
          <PercentileResults />
        </ErrorBoundary>
      </Container>
    </main>
  )
}
