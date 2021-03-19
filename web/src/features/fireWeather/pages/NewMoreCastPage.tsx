import React, { useState, useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { useLocation } from 'react-router-dom'
import { makeStyles } from '@material-ui/core/styles'

import { PageHeader } from 'components'
import { getStationCodesFromUrl, getTimeOfInterestFromUrl } from 'utils/url'
import { fetchWxStations } from 'features/percentileCalculator/slices/stationsSlice'
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
    fontSize: '2rem'
  },
  sidePanel: (props: { showSide: boolean }) => ({
    order: 2,
    width: props.showSide ? 700 : 0,
    overflowX: 'hidden',
    transition: '0.4s',
    boxShadow:
      '0px 3px 3px -2px rgb(0 0 0 / 20%), 0px 3px 4px 0px rgb(0 0 0 / 14%), 0px 1px 8px 0px rgb(0 0 0 / 12%)'
  }),
  sidePanelContent: {
    width: 700,
    padding: 13,
    position: 'relative'
  },
  sidePanelCloseBtn: {
    position: 'absolute',
    top: 0,
    left: 10,
    fontSize: 22,
    cursor: 'pointer',
    fontWeight: 'bold'
  }
}))

const MoreCastPage = () => {
  const dispatch = useDispatch()
  const location = useLocation()

  const codesFromQuery = getStationCodesFromUrl(location.search)
  const toiFromQuery = getTimeOfInterestFromUrl(location.search)

  const [showSide, setShowSide] = useState(codesFromQuery.length > 0)
  const classes = useStyles({ showSide })
  const openSide = () => setShowSide(true)

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
      <PageHeader title="MoreCast" productName="MoreCast" noContainer padding={25} />
      <div className={classes.nav}>
        <WxDataForm
          codesFromQuery={codesFromQuery}
          toiFromQuery={toiFromQuery}
          openSide={openSide}
        />
      </div>
      <div className={classes.content}>
        <div className={classes.map}>map</div>
        <div className={classes.sidePanel}>
          <div className={classes.sidePanelContent}>
            <div
              className={classes.sidePanelCloseBtn}
              onClick={() => setShowSide(false)}
              role="button"
            >
              &times;
            </div>
            <WxDataDisplays stationCodes={codesFromQuery} timeOfInterest={toiFromQuery} />
          </div>
        </div>
      </div>
    </main>
  )
}

export default React.memo(MoreCastPage)
