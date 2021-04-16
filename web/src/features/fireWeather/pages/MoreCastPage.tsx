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
          <WeatherMap redrawFlag={showSidePanel} />
        </div>
        <SidePanel
          show={showSidePanel}
          closeSidePanel={closeSidePanel}
          handleToggleView={handleToggleView}
          showTableView={showTableView}
        >
          <NetworkErrorMessages />
          <WxDataDisplays
            stationCodes={codesFromQuery}
            timeOfInterest={toiFromQuery}
            showTableView={showTableView}
          />
        </SidePanel>
      </div>
    </main>
  )
}

export default React.memo(MoreCastPage)
