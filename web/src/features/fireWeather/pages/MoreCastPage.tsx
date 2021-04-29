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
import SidePanel, { SidePanelEnum } from 'features/fireWeather/components/SidePanel'
import NetworkErrorMessages from 'features/fireWeather/components/NetworkErrorMessages'
import WeatherMap from 'features/fireWeather/components/maps/WeatherMap'
import ExpandableContainer from 'features/fireWeather/components/ExpandableContainer'
import { getStations } from 'api/stationAPI'
import { PARTIAL_WIDTH, FULL_WIDTH, CENTER_OF_BC } from 'utils/constants'
import { RedrawCommand } from 'features/map/Map'

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

  const shouldInitiallyShowSidePanel = codesFromQuery.length > 0
  const [showSidePanel, setShowSidePanel] = useState(shouldInitiallyShowSidePanel)
  const [sidePanelWidth, setSidePanelWidth] = useState(
    shouldInitiallyShowSidePanel
      ? codesFromQuery.length > 1
        ? FULL_WIDTH
        : PARTIAL_WIDTH
      : 0
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
  const openSidePanel = () => {
    setShowSidePanel(true)
    setSidePanelWidth(PARTIAL_WIDTH)
  }
  const closeSidePanel = () => setShowSidePanel(false)

  const [showTableView, toggleTableView] = useState(
    codesFromQuery.length > 1 ? SidePanelEnum.Comparison : SidePanelEnum.Tables
  )
  const handleToggleView = (
    _: React.MouseEvent<HTMLElement>,
    newTableView: SidePanelEnum
  ) => {
    if (newTableView !== null) {
      toggleTableView(newTableView)
    }
  }

  useEffect(() => {
    if (codesFromQuery.length > 1) {
      toggleTableView(SidePanelEnum.Comparison)
    } else {
      toggleTableView(SidePanelEnum.Tables)
    }
  }, [codesFromQuery.length])

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
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
    <main className={classes.main}>
      <PageHeader title="MoreCast" productName="MoreCast" noContainer padding={25} />
      <div className={classes.nav}>
        <WxDataForm
          codesFromQuery={codesFromQuery}
          toiFromQuery={toiFromQuery}
          openSidePanel={openSidePanel}
        />
      </div>
      <div className={classes.content}>
        <div className={classes.map}>
          <WeatherMap
            redrawFlag={getRedrawCommand()}
            isCollapsed={sidePanelWidth === FULL_WIDTH}
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
          <SidePanel
            show={showSidePanel}
            closeSidePanel={closeSidePanel}
            handleToggleView={handleToggleView}
            showTableView={showTableView}
            stationCodes={codesFromQuery}
          >
            <NetworkErrorMessages />
            <WxDataDisplays
              stationCodes={codesFromQuery}
              timeOfInterest={toiFromQuery}
              expandedOrCollapsed={getRedrawCommand()}
              showTableView={showTableView}
            />
          </SidePanel>
        </ExpandableContainer>
      </div>
      <div className={classes.legend}>
        <AccuracyColorLegend show={sidePanelWidth <= PARTIAL_WIDTH} />
      </div>
    </main>
  )
}

export default React.memo(MoreCastPage)
