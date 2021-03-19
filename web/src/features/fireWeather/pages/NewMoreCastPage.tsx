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

const useStyles = makeStyles(theme => ({
  main: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh'
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
  navTitle: {
    fontSize: '1.3rem',
    marginRight: 25
  },
  content: {
    display: 'flex',
    flexGrow: 1
  },
  map: {
    order: 1,
    flexGrow: 1,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'grey',
    fontSize: '2rem'
  },
  sidePanel: (props: { showSide: boolean }) => ({
    order: 2,
    width: props.showSide ? 650 : 0,
    overflowX: 'hidden',
    transition: '0.5s',
    backgroundColor: 'lightblue'
  }),
  sidePanelContent: {
    width: 650,
    padding: 12
  }
}))

const MoreCastPage = () => {
  const [showSide, setShowSide] = useState(false)
  const classes = useStyles({ showSide })
  const dispatch = useDispatch()
  const location = useLocation()

  const codesFromQuery = getStationCodesFromUrl(location.search)
  const toiFromQuery = getTimeOfInterestFromUrl(location.search)

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
    <main className={classes.main}>
      <PageHeader
        title="Predictive Services Unit"
        productName="MoreCast"
        noContainer
        padding={25}
      />
      <div className={classes.nav}>
        <div className={classes.navTitle}>MoreCast</div>
        <WxDataForm codesFromQuery={codesFromQuery} toiFromQuery={toiFromQuery} />
        <button onClick={() => setShowSide(show => !show)}>toggle</button>
      </div>
      <div className={classes.content}>
        <div className={classes.map}>map</div>
        <div className={classes.sidePanel}>
          <div className={classes.sidePanelContent}>
            <button onClick={() => setShowSide(false)}>close</button>
            <h2>Graph and Table here</h2>
          </div>
        </div>
      </div>
    </main>
  )
}

export default React.memo(MoreCastPage)
