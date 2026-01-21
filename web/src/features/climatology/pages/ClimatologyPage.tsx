import React, { useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { Container, GeneralHeader, ErrorBoundary } from 'components'
import { ErrorMessage } from 'components/ErrorMessage'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource, GeoJsonStation } from 'api/stationAPI'
import { AppDispatch } from 'app/store'
import { selectClimatology, selectPercentileStations } from 'app/rootReducer'
import { CLIMATOLOGY_DOC_TITLE, CLIMATOLOGY_NAME } from 'utils/constants'

import ClimatologyControls from '../components/ClimatologyControls'
import ClimatologyChart from '../components/ClimatologyChart'
import {
  AggregationPeriod,
  ReferencePeriod,
  STANDARD_REFERENCE_PERIODS,
  WeatherVariable
} from '../interfaces'
import { fetchClimatology, resetClimatologyResult } from '../slices/climatologySlice'

const currentYear = new Date().getFullYear()

const ClimatologyPage: React.FC = () => {
  const dispatch: AppDispatch = useDispatch()
  const { loading, error, result } = useSelector(selectClimatology)
  const { loading: stationsLoading, stations, error: stationsError } = useSelector(selectPercentileStations)

  // Form state
  const [selectedStationCode, setSelectedStationCode] = useState<number | null>(null)
  const [variable, setVariable] = useState<WeatherVariable>(WeatherVariable.HOURLY_TEMPERATURE)
  const [aggregation, setAggregation] = useState<AggregationPeriod>(AggregationPeriod.DAILY)
  const [referencePeriod, setReferencePeriod] = useState<ReferencePeriod>(STANDARD_REFERENCE_PERIODS[0])
  const [comparisonYear, setComparisonYear] = useState<number>(currentYear)

  // Transform stations for the dropdown
  const stationOptions = useMemo(
    () =>
      (stations as GeoJsonStation[]).map(station => ({
        name: station.properties.name,
        code: station.properties.code
      })),
    [stations]
  )

  // Fetch stations on mount
  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.unspecified))
  }, [dispatch])

  // Set document title
  useEffect(() => {
    document.title = CLIMATOLOGY_DOC_TITLE
  }, [])

  const handleFetch = () => {
    if (selectedStationCode === null) return

    dispatch(
      fetchClimatology(selectedStationCode, variable, aggregation, referencePeriod, comparisonYear)
    )
  }

  const handleReset = () => {
    setSelectedStationCode(null)
    setVariable(WeatherVariable.HOURLY_TEMPERATURE)
    setAggregation(AggregationPeriod.DAILY)
    setReferencePeriod(STANDARD_REFERENCE_PERIODS[0])
    setComparisonYear(currentYear)
    dispatch(resetClimatologyResult())
  }

  return (
    <main data-testid="climatology-page">
      <GeneralHeader isBeta={true} spacing={1} title={CLIMATOLOGY_NAME} />
      <Container maxWidth={false} sx={{ paddingTop: '0.5em' }}>
        <ClimatologyControls
          stations={stationOptions}
          stationsLoading={stationsLoading}
          selectedStationCode={selectedStationCode}
          onStationChange={setSelectedStationCode}
          variable={variable}
          aggregation={aggregation}
          referencePeriod={referencePeriod}
          comparisonYear={comparisonYear}
          onVariableChange={setVariable}
          onAggregationChange={setAggregation}
          onReferencePeriodChange={setReferencePeriod}
          onComparisonYearChange={setComparisonYear}
          onFetch={handleFetch}
          onReset={handleReset}
          loading={loading}
        />

        {stationsError && <ErrorMessage error={stationsError} context="while fetching weather stations" />}
        {error && <ErrorMessage error={error} context="while fetching climatology data" />}

        <ErrorBoundary>
          <ClimatologyChart data={result} loading={loading} />
        </ErrorBoundary>
      </Container>
    </main>
  )
}

export default React.memo(ClimatologyPage)
