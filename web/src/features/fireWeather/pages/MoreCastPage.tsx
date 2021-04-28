import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useLocation } from 'react-router-dom'
import { makeStyles } from '@material-ui/core/styles'

import { PageHeader } from 'components'
import { getStationCodesFromUrl, getTimeOfInterestFromUrl } from 'utils/url'
import { fetchWxStations, selectStations} from 'features/stations/slices/stationsSlice'
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
import { selectFireWeatherStations } from 'app/rootReducer'


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

  const selectedCodes: number[] = codesFromQuery
  const {
    selectedStationsByCode
  } = useSelector(selectFireWeatherStations)

  // codesOfRetrievedStationData[] represents the station codes for which weather data has
  // been retrieved (and therefore the station should appear in WxDataDisplays)
  const [codesOfRetrievedStationData, setCodesOfRetrievedStationData] = useState<
    number[]
  >(codesFromQuery)
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
    dispatch(selectStations(codesFromQuery))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedStationsByCode.length > 0) {
      dispatch(fetchObservations(selectedStationsByCode, timeOfInterest))
      dispatch(fetchForecasts(selectedStationsByCode, timeOfInterest))
      dispatch(fetchForecastSummaries(selectedStationsByCode, timeOfInterest))
      dispatch(fetchHighResModels(selectedStationsByCode, timeOfInterest))
      dispatch(fetchHighResModelSummaries(selectedStationsByCode, timeOfInterest))
      dispatch(fetchRegionalModels(selectedStationsByCode, timeOfInterest))
      dispatch(fetchRegionalModelSummaries(selectedStationsByCode, timeOfInterest))
      dispatch(fetchGlobalModelsWithBiasAdj(selectedStationsByCode, timeOfInterest))
      dispatch(fetchGlobalModelSummaries(selectedStationsByCode, timeOfInterest))
    }
    // Update local state to match with the query url
    setCodesOfRetrievedStationData(selectedStationsByCode)
    setTimeOfInterest(timeOfInterest)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main className={classes.main}>
      <PageHeader title="MoreCast" productName="MoreCast" noContainer padding={25} />
      <div className={classes.nav}>
        <WxDataForm
          stationCodesQuery={selectedStationsByCode}
          timeOfInterestQuery={timeOfInterest}
          setSelectedTimeOfInterest={setTimeOfInterest}
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
