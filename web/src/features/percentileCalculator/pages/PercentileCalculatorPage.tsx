import React, { useEffect, useState } from 'react'
import { useDispatch } from 'react-redux'
import { useLocation, useNavigate } from 'react-router-dom'

import { PercentileHeader, PageTitle, Container, ErrorBoundary } from 'components'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import WxStationDropdown from 'features/percentileCalculator/components/WxStationDropdown'
import { PercentileTextfield } from 'features/percentileCalculator/components/PercentileTextfield'
import { fetchPercentiles, resetPercentilesResult } from 'features/percentileCalculator/slices/percentilesSlice'
import { PercentileActionButtons } from 'features/percentileCalculator/components/PercentileActionButtons'
import PercentileResults from 'features/percentileCalculator/components/PercentileResults'
import { TimeRangeSlider, yearWhenTheCalculationIsDone } from 'features/percentileCalculator/components/TimeRangeSlider'
import { getStationCodesFromUrl, stationCodeQueryKey } from 'utils/url'
import { getStations, StationSource } from 'api/stationAPI'
import { AppDispatch } from 'app/store'
import { PERCENTILE_CALC_DOC_TITLE } from 'utils/constants'

const defaultTimeRange = 10
const defaultPercentile = 90

const PercentileCalculatorPage = () => {
  const dispatch: AppDispatch = useDispatch()
  const location = useLocation()
  const navigate = useNavigate()

  const codesFromQuery = getStationCodesFromUrl(location.search)
  const [stationCodes, setStationCodes] = useState<number[]>(codesFromQuery)
  const [timeRange, setTimeRange] = useState<number>(defaultTimeRange)
  const yearRange = {
    start: yearWhenTheCalculationIsDone - timeRange,
    end: yearWhenTheCalculationIsDone - 1
  }

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.local_storage))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (codesFromQuery.length > 0) {
      dispatch(fetchPercentiles(codesFromQuery, defaultPercentile, yearRange))
    } else {
      dispatch(resetPercentilesResult())
    }

    // Update local state to match with the url query
    setStationCodes(codesFromQuery)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  const onCalculateClick = () => {
    // Update the url query with the new station codes
    navigate({ search: `${stationCodeQueryKey}=${stationCodes.join(',')}` })
  }

  const onResetClick = () => {
    navigate({ search: undefined })
    setTimeRange(defaultTimeRange)
  }

  const shouldCalcBtnDisabled = stationCodes.length === 0

  useEffect(() => {
    document.title = PERCENTILE_CALC_DOC_TITLE
  }, [])

  return (
    <main data-testid="percentile-calculator-page">
      <PercentileHeader title="Predictive Services Unit" productName="Percentile Calculator" />
      <PageTitle title="Percentile Calculator" />
      <Container>
        <WxStationDropdown stationCodes={stationCodes} onChange={setStationCodes} />

        <TimeRangeSlider timeRange={timeRange} onYearRangeChange={setTimeRange} />

        <PercentileTextfield />

        <PercentileActionButtons
          calcDisabled={shouldCalcBtnDisabled}
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

export default React.memo(PercentileCalculatorPage)
