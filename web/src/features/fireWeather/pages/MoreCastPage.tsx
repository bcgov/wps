import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useLocation } from 'react-router-dom'
import { makeStyles } from '@material-ui/core/styles'

import { PageHeader } from 'components'
import { getStationCodesFromUrl, getTimeOfInterestFromUrl } from 'utils/url'
import { fetchWxStations, selectStations } from 'features/stations/slices/stationsSlice'
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
import ExpandableContainer from 'features/fireWeather/components/ExpandableContainer'
import { getDetailedStations, getStations, StationSource } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import { PARTIAL_WIDTH, FULL_WIDTH, CENTER_OF_BC } from 'utils/constants'
import { RedrawCommand } from 'features/map/Map'
import StationAccuracyForDate from '../components/StationAccuracyForDate'

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

  const { selectedStationsByCode } = useSelector(selectFireWeatherStations)

  // retrievedStationDataCodes[] represents the station codes for which weather data has
  // been retrieved (and therefore the station should appear in WxDataDisplays)
  const [retrievedStationDataCodes, setRetrievedStationDataCodes] = useState<number[]>(
    codesFromQuery
  )
  const [timeOfInterest, setTimeOfInterest] = useState(toiFromQuery)
  const shouldInitiallyShowSidePanel = codesFromQuery.length > 0
  const [showSidePanel, setShowSidePanel] = useState(shouldInitiallyShowSidePanel)
  const [sidePanelWidth, setSidePanelWidth] = useState(
    shouldInitiallyShowSidePanel ? PARTIAL_WIDTH : 0
  )

  const [mapCenter, setMapCenter] = useState(CENTER_OF_BC)
  const expandSidePanel = () => setSidePanelWidth(FULL_WIDTH)
  const collapseSidePanel = () => setSidePanelWidth(PARTIAL_WIDTH)

  // Callback to set the latest center coordinates when side panel is collapsed
  // to preserve any panning of the map by the user before panel was expanded.
  const setNewMapCenter = (newMapCenter: number[]) => {
    setMapCenter(newMapCenter)
  }

  const getRedrawCommand = (): RedrawCommand | undefined => {
    return !showSidePanel || sidePanelWidth === PARTIAL_WIDTH
      ? { redraw: true }
      : undefined
  }
  const shouldOpenSidePanel = (openOrClose: boolean) => {
    if (openOrClose) {
      setShowSidePanel(true)
      setSidePanelWidth(PARTIAL_WIDTH)
    } else {
      closeSidePanel()
    }
  }
  const closeSidePanel = () => setShowSidePanel(false)

  const [showTableView, toggleTableView] = useState('true')
  const handleToggleView = (_: React.MouseEvent<HTMLElement>, newTableView: string) => {
    toggleTableView(newTableView.endsWith('true') ? 'true' : 'false')
  }

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
    dispatch(selectStations(codesFromQuery))
    setTimeOfInterest(toiFromQuery)
    dispatch(
      fetchWxStations(getDetailedStations, StationSource.unspecified, toiFromQuery)
    )
    if (codesFromQuery.length > 0) {
      dispatch(fetchObservations(codesFromQuery, timeOfInterest))
      dispatch(fetchForecasts(codesFromQuery, timeOfInterest))
      dispatch(fetchForecastSummaries(codesFromQuery, timeOfInterest))
      dispatch(fetchHighResModels(codesFromQuery, timeOfInterest))
      dispatch(fetchHighResModelSummaries(codesFromQuery, timeOfInterest))
      dispatch(fetchRegionalModels(codesFromQuery, timeOfInterest))
      dispatch(fetchRegionalModelSummaries(codesFromQuery, timeOfInterest))
      dispatch(fetchGlobalModelsWithBiasAdj(codesFromQuery, timeOfInterest))
      dispatch(fetchGlobalModelSummaries(codesFromQuery, timeOfInterest))
      setRetrievedStationDataCodes(codesFromQuery)
    }

    if (codesFromQuery.length > 0) {
      // Open the side panel
      shouldOpenSidePanel(true)
    } else {
      // Close side panel if we do not care about specific stations
      shouldOpenSidePanel(false)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    dispatch(selectStations(codesFromQuery))
    if (codesFromQuery.length > 0) {
      dispatch(fetchObservations(codesFromQuery, timeOfInterest))
      dispatch(fetchForecasts(codesFromQuery, timeOfInterest))
      dispatch(fetchForecastSummaries(codesFromQuery, timeOfInterest))
      dispatch(fetchHighResModels(codesFromQuery, timeOfInterest))
      dispatch(fetchHighResModelSummaries(codesFromQuery, timeOfInterest))
      dispatch(fetchRegionalModels(codesFromQuery, timeOfInterest))
      dispatch(fetchRegionalModelSummaries(codesFromQuery, timeOfInterest))
      dispatch(fetchGlobalModelsWithBiasAdj(codesFromQuery, timeOfInterest))
      dispatch(fetchGlobalModelSummaries(codesFromQuery, timeOfInterest))
    }
    // Update local state to match with the query url
    setRetrievedStationDataCodes(codesFromQuery)
    setTimeOfInterest(timeOfInterest)
    dispatch(
      fetchWxStations(getDetailedStations, StationSource.unspecified, toiFromQuery)
    )
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main className={classes.main}>
      <PageHeader title="MoreCast" productName="MoreCast" noContainer padding={25} />
      <div className={classes.nav}>
        <WxDataForm
          stationCodesQuery={selectedStationsByCode}
          toiFromQuery={toiFromQuery}
          shouldOpenSidePanel={shouldOpenSidePanel}
        />
      </div>
      <div className={classes.content}>
        <div className={classes.map}>
          <WeatherMap
            redrawFlag={getRedrawCommand()}
            isCollapsed={sidePanelWidth === FULL_WIDTH}
            toiFromQuery={toiFromQuery}
            center={mapCenter}
            setMapCenter={setNewMapCenter}
          />
        </div>
        <ExpandableContainer
          open={showSidePanel}
          close={closeSidePanel}
          expand={expandSidePanel}
          collapse={collapseSidePanel}
          currentWidth={sidePanelWidth}
        >
          <NetworkErrorMessages />
          <SidePanel handleToggleView={handleToggleView} showTableView={showTableView}>
            <NetworkErrorMessages />
            <WxDataDisplays
              stationCodes={retrievedStationDataCodes}
              timeOfInterest={toiFromQuery}
              expandedOrCollapsed={getRedrawCommand()}
              showTableView={showTableView}
            />
          </SidePanel>
        </ExpandableContainer>
      </div>
      {(sidePanelWidth <= PARTIAL_WIDTH || showSidePanel === false) && (
        <div className={classes.legend} data-testid="legend">
          <AccuracyColorLegend />
          <StationAccuracyForDate toiFromQuery={toiFromQuery} />
        </div>
      )}
    </main>
  )
}

export default React.memo(MoreCastPage)
