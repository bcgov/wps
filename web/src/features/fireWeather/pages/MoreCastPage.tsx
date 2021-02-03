import React, { useEffect, useState } from 'react'
import { useDispatch } from 'react-redux'
import { useLocation, useHistory } from 'react-router-dom'
import { makeStyles } from '@material-ui/core/styles'

import { PageHeader, PageTitle, Container } from 'components'
import WxStationDropdown from 'features/stations/components/WxStationDropdown'
import WxDataDisplays from 'features/fireWeather/components/WxDataDisplays'
import TimeOfInterestPicker from 'features/fireWeather/components/TimeOfInterestPicker'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { fetchGlobalModelsWithBiasAdj } from 'features/fireWeather/slices/modelsSlice'
import { fetchObservations } from 'features/fireWeather/slices/observationsSlice'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { fetchForecasts } from 'features/fireWeather/slices/forecastsSlice'
import { fetchGlobalModelSummaries } from 'features/fireWeather/slices/modelSummariesSlice'
import { fetchForecastSummaries } from 'features/fireWeather/slices/forecastSummariesSlice'
import { fetchHighResModels } from 'features/fireWeather/slices/highResModelsSlice'
import { fetchHighResModelSummaries } from 'features/fireWeather/slices/highResModelSummariesSlice'
import { fetchRegionalModels } from 'features/fireWeather/slices/regionalModelsSlice'
import { fetchRegionalModelSummaries } from 'features/fireWeather/slices/regionalModelSummariesSlice'
import { getStationCodesFromUrl, stationCodeQueryKey } from 'utils/url'
import { formatDateInISO } from 'utils/date'

const useStyles = makeStyles({
  stationDropdown: {
    marginBottom: 10
  }
})

const MoreCastPage = () => {
  const classes = useStyles()
  const dispatch = useDispatch()
  const location = useLocation()
  const history = useHistory()

  const codesFromQuery = getStationCodesFromUrl(location.search)
  const [selectedCodes, setSelectedCodes] = useState<number[]>(codesFromQuery)
  const [timeOfInterest, setTimeOfInterest] = useState(new Date())

  useEffect(() => {
    dispatch(fetchWxStations())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (codesFromQuery.length > 0) {
      const isoTOI = formatDateInISO(timeOfInterest)
      dispatch(fetchObservations(codesFromQuery, isoTOI))
      dispatch(fetchForecasts(codesFromQuery, isoTOI))
      dispatch(fetchForecastSummaries(codesFromQuery, isoTOI))
      dispatch(fetchHighResModels(codesFromQuery, isoTOI))
      dispatch(fetchHighResModelSummaries(codesFromQuery, isoTOI))
      dispatch(fetchRegionalModels(codesFromQuery, isoTOI))
      dispatch(fetchRegionalModelSummaries(codesFromQuery, isoTOI))
      dispatch(fetchGlobalModelsWithBiasAdj(codesFromQuery, isoTOI))
      dispatch(fetchGlobalModelSummaries(codesFromQuery, isoTOI))
    }

    // Update local state to match with the url query
    setSelectedCodes(codesFromQuery)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  const onSubmitClick = () => {
    // Update the url query with the new station codes
    history.push({ search: `${stationCodeQueryKey}=${selectedCodes.join(',')}` })

    // Create matomo event
    // NOTE: This section is proof of concept - strongly consider re-factoring when adding other events.
    // TODO: Re-evaluate this way of implementing Matomo once we know more about it.
    if (window._mtm) {
      // Create event, and push list of stations to the matomo data layer.
      // see: https://developer.matomo.org/guides/tagmanager/integration-plugin#supporting-the-data-layer
      window._mtm.push({ event: 'getWeatherData', stationCodes: selectedCodes })
    }
  }

  const shouldGetBtnDisabled = selectedCodes.length === 0

  return (
    <main>
      <PageHeader title="Predictive Services Unit" productName="MoreCast" />
      <PageTitle title="MoreCast - Weather Forecast Validation Tool" />
      <Container>
        <form noValidate>
          <WxStationDropdown
            className={classes.stationDropdown}
            stationCodes={selectedCodes}
            onChange={setSelectedCodes}
          />
          <TimeOfInterestPicker
            timeOfInterest={timeOfInterest}
            onChange={setTimeOfInterest}
          />
          <GetWxDataButton onBtnClick={onSubmitClick} disabled={shouldGetBtnDisabled} />
        </form>

        <WxDataDisplays timeOfInterest={timeOfInterest} stationCodes={codesFromQuery} />
      </Container>
    </main>
  )
}

export default React.memo(MoreCastPage)
