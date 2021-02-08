import React, { useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { useLocation } from 'react-router-dom'

import { PageHeader, PageTitle, Container } from 'components'
import WxDataDisplays from 'features/fireWeather/components/WxDataDisplays'
import WxDataForm from 'features/fireWeather/components/WxDataForm'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { fetchGlobalModelsWithBiasAdj } from 'features/fireWeather/slices/modelsSlice'
import { fetchObservations } from 'features/fireWeather/slices/observationsSlice'
import { fetchForecasts } from 'features/fireWeather/slices/forecastsSlice'
import { fetchGlobalModelSummaries } from 'features/fireWeather/slices/modelSummariesSlice'
import { fetchForecastSummaries } from 'features/fireWeather/slices/forecastSummariesSlice'
import { fetchHighResModels } from 'features/fireWeather/slices/highResModelsSlice'
import { fetchHighResModelSummaries } from 'features/fireWeather/slices/highResModelSummariesSlice'
import { fetchRegionalModels } from 'features/fireWeather/slices/regionalModelsSlice'
import { fetchRegionalModelSummaries } from 'features/fireWeather/slices/regionalModelSummariesSlice'
import { getStationCodesFromUrl, getTimeOfInterestFromUrl } from 'utils/url'

const MoreCastPage = () => {
  const dispatch = useDispatch()
  const location = useLocation()

  const codesFromQuery = getStationCodesFromUrl(location.search)
  const toiFromQuery = getTimeOfInterestFromUrl(location.search)
  const timeOfInterest = new Date(toiFromQuery)

  useEffect(() => {
    dispatch(fetchWxStations())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (codesFromQuery.length > 0) {
      dispatch(fetchObservations(codesFromQuery, toiFromQuery))
      dispatch(fetchForecasts(codesFromQuery, toiFromQuery))
      dispatch(fetchForecastSummaries(codesFromQuery, toiFromQuery))
      dispatch(fetchHighResModels(codesFromQuery, toiFromQuery))
      dispatch(fetchHighResModelSummaries(codesFromQuery, toiFromQuery))
      dispatch(fetchRegionalModels(codesFromQuery, toiFromQuery))
      dispatch(fetchRegionalModelSummaries(codesFromQuery, toiFromQuery))
      dispatch(fetchGlobalModelsWithBiasAdj(codesFromQuery, toiFromQuery))
      dispatch(fetchGlobalModelSummaries(codesFromQuery, toiFromQuery))
    }
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main>
      <PageHeader title="Predictive Services Unit" productName="MoreCast" />
      <PageTitle title="MoreCast - Weather Forecast Validation Tool" />
      <Container>
        <WxDataForm codesFromQuery={codesFromQuery} toiFromQuery={toiFromQuery} />
        <WxDataDisplays stationCodes={codesFromQuery} timeOfInterest={timeOfInterest} />
      </Container>
    </main>
  )
}

export default React.memo(MoreCastPage)
