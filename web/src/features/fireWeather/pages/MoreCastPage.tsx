import React, { useState, useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { useLocation } from 'react-router-dom'
import { makeStyles } from '@material-ui/core/styles'

import { PageHeader } from 'components'
import { getStationCodesFromUrl, getTimeOfInterestFromUrl } from 'utils/url'
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
import WxDataDisplays from 'features/fireWeather/components/WxDataDisplays'
import WxDataForm from 'features/fireWeather/components/WxDataForm'
import AccuracyColorLegend from 'features/fireWeather/components/AccuracyColorLegend'
import SidePanel from 'features/fireWeather/components/SidePanel'
import NetworkErrorMessages from 'features/fireWeather/components/NetworkErrorMessages'
import WeatherMap from 'features/fireWeather/components/maps/WeatherMap'
import { getStations } from 'api/stationAPI'

const useStyles = makeStyles(theme => ({
  main: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh'
  },
  nav: {
    background: theme.palette.primary.light,
    color: theme.palette.primary.contrastText,
    minHeight: 60,
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    paddingLeft: 25,
    paddingRight: 25
  },
  content: {
    flexGrow: 1,
    display: 'flex',
    overflowY: 'auto'
  },
  map: {
    order: 1,
    flexGrow: 1,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },
  legend: {
    display: 'flex',
    alignItems: 'flex-end',
    backgroundColor: theme.palette.primary.light
  }
}))

const MoreCastPage = () => {
  const classes = useStyles()
  const dispatch = useDispatch()
  const location = useLocation()

  const codesFromQuery = getStationCodesFromUrl(location.search)
  const toiFromQuery = getTimeOfInterestFromUrl(location.search)

  // selectedCodes[] represents the station codes that the user has selected from
  // either the station dropdown or the map. Weather data for these stations
  // has not necessarily been retrieved
  const [selectedCodes, _setSelectedCodes] = useState<number[]>(codesFromQuery)
  // need to customize setSelectedCodes function to remove duplicate station codes
  // (can happen if a station is selected from the map twice, or from the map and
  // the dropdown)
  const setSelectedCodes = (selectedCodes: number[]) => {
    const selectedCodesSet = new Set(selectedCodes)
    selectedCodes = Array.from(selectedCodesSet.values())
    _setSelectedCodes(selectedCodes)
  }
  // codesOfRetrievedStationData[] represents the station codes for which weather data has
  // been retrieved (and therefore the station should appear in WxDataDisplays)
  const [codesOfRetrievedStationData, setCodesOfRetrievedStationData] = useState<number[]>(codesFromQuery)
  const [timeOfInterest, setTimeOfInterest] = useState(toiFromQuery)
  const shouldInitiallyShowSidePanel = selectedCodes.length > 0
  const [showSidePanel, setShowSidePanel] = useState(shouldInitiallyShowSidePanel)
  const openSidePanel = () => setShowSidePanel(true)
  const closeSidePanel = () => setShowSidePanel(false)

  const [showTableView, toggleTableView] = useState('true')
  const handleToggleView = (_: React.MouseEvent<HTMLElement>, newTableView: string) => {
    toggleTableView(newTableView.endsWith('true') ? 'true' : 'false')
  }

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedCodes.length > 0) {
      dispatch(fetchObservations(selectedCodes, timeOfInterest))
      dispatch(fetchForecasts(selectedCodes, timeOfInterest))
      dispatch(fetchForecastSummaries(selectedCodes, timeOfInterest))
      dispatch(fetchHighResModels(selectedCodes, timeOfInterest))
      dispatch(fetchHighResModelSummaries(selectedCodes, timeOfInterest))
      dispatch(fetchRegionalModels(selectedCodes, timeOfInterest))
      dispatch(fetchRegionalModelSummaries(selectedCodes, timeOfInterest))
      dispatch(fetchGlobalModelsWithBiasAdj(selectedCodes, timeOfInterest))
      dispatch(fetchGlobalModelSummaries(selectedCodes, timeOfInterest))
    }
    // Update local state to match with the query url
    setSelectedCodes(selectedCodes)
    setCodesOfRetrievedStationData(selectedCodes)
    setTimeOfInterest(timeOfInterest)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main className={classes.main}>
      <PageHeader title="MoreCast" productName="MoreCast" noContainer padding={25} />
      <div className={classes.nav}>
        <WxDataForm
          stationCodesQuery={selectedCodes}
          timeOfInterestQuery={timeOfInterest}
          setSelectedStationCodes={_setSelectedCodes}
          setSelectedTimeOfInterest={setTimeOfInterest}
          openSidePanel={openSidePanel}
        />
      </div>
      <div className={classes.content}>
        <div className={classes.map}>
          <WeatherMap
            redrawFlag={showSidePanel}
            selectedStationCodes={selectedCodes}
            setSelectedStationCodes={setSelectedCodes}
          />
        </div>
        <SidePanel
          show={showSidePanel}
          closeSidePanel={closeSidePanel}
          handleToggleView={handleToggleView}
          showTableView={showTableView}
        >
          <NetworkErrorMessages />
          <WxDataDisplays
            stationCodes={codesOfRetrievedStationData}
            timeOfInterest={timeOfInterest}
            showTableView={showTableView}
          />
        </SidePanel>
      </div>
      <div className={classes.legend}>
        <AccuracyColorLegend />
      </div>
    </main>
  )
}

export default React.memo(MoreCastPage)
