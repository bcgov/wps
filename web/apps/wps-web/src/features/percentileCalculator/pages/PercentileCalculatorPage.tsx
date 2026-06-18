import { getStations, StationSource } from '@wps/api/stationAPI'
import { Container } from '@wps/ui/Container'
import { ErrorBoundary } from '@wps/ui/ErrorBoundary'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { PERCENTILE_CALC_DOC_TITLE, PERCENTILE_CALC_NAME } from '@wps/utils/constants'
import { getStationCodesFromUrl, stationCodeQueryKey } from '@wps/utils/url'
import type { AppDispatch } from 'app/store'
import { PercentileActionButtons } from 'features/percentileCalculator/components/PercentileActionButtons'
import PercentileResults from 'features/percentileCalculator/components/PercentileResults'
import { PercentileTextfield } from 'features/percentileCalculator/components/PercentileTextfield'
import { TimeRangeSlider, yearWhenTheCalculationIsDone } from 'features/percentileCalculator/components/TimeRangeSlider'
import WxStationDropdown from 'features/percentileCalculator/components/WxStationDropdown'
import { fetchPercentiles, resetPercentilesResult } from 'features/percentileCalculator/slices/percentilesSlice'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import React, { useEffect, useMemo, useState } from 'react'
import { useDispatch } from 'react-redux'
import { useLocation, useNavigate } from 'react-router-dom'

const defaultTimeRange = 10
const defaultPercentile = 90

const PercentileCalculatorPage = () => {
  const dispatch: AppDispatch = useDispatch()
  const location = useLocation()
  const navigate = useNavigate()

  const codesFromQuery = useMemo(() => getStationCodesFromUrl(location.search), [location.search])
  const [stationCodes, setStationCodes] = useState<number[]>(codesFromQuery)
  const [timeRange, setTimeRange] = useState<number>(defaultTimeRange)
  const yearRange = useMemo(
    () => ({
      start: yearWhenTheCalculationIsDone - (timeRange - 1),
      end: yearWhenTheCalculationIsDone
    }),
    [timeRange]
  )

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.unspecified))
  }, [dispatch])

  useEffect(() => {
    if (codesFromQuery.length > 0) {
      dispatch(fetchPercentiles(codesFromQuery, defaultPercentile, yearRange))
    } else {
      dispatch(resetPercentilesResult())
    }

    // Update local state to match with the url query
    setStationCodes(codesFromQuery)
  }, [codesFromQuery, dispatch, yearRange])

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
      <GeneralHeader isBeta={false} spacing={1} title={PERCENTILE_CALC_NAME} />
      <Container sx={{ paddingTop: '0.5em' }}>
        <WxStationDropdown stationCodes={stationCodes} onChange={setStationCodes} />

        <TimeRangeSlider timeRange={timeRange} onYearRangeChange={setTimeRange} />

        <PercentileTextfield />

        <PercentileActionButtons
          calcDisabled={shouldCalcBtnDisabled}
          onCalculateClick={onCalculateClick}
          onResetClick={onResetClick}
        />

        <ErrorBoundary>
          <PercentileResults timeRange={timeRange} />
        </ErrorBoundary>
      </Container>
    </main>
  )
}

export default React.memo(PercentileCalculatorPage)
