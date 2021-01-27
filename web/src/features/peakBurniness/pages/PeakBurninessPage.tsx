import React, { useRef, useEffect, useState } from 'react'
import ReactDOMServer from 'react-dom/server'
import { useDispatch, useSelector } from 'react-redux'
import { Container, PageHeader, PageTitle } from 'components'
import { Paper, makeStyles } from '@material-ui/core'
import { ErrorBoundary } from 'components'
import PeakValuesResults from 'features/peakBurniness/components/tables/PeakValuesResults'
import WxStationDropdown from 'features/stations/components/WxStationDropdown'
import { useHistory, useLocation } from 'react-router-dom'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStationCodesFromUrl, stationCodeQueryKey } from 'utils/url'
import { fetchPeakValues, resetPeakValuesResult } from '../slices/peakBurninessSlice'
import { StationPeakValues } from 'api/peakBurninessAPI'
import { Station } from 'api/stationAPI'
import { selectPeakBurninessValues, selectStations } from 'app/rootReducer'

const useStyles = makeStyles({
  displays: {
    marginTop: 16
  },
  paper: {
    paddingLeft: 18,
    paddingRight: 18,
    paddingBottom: 8,
    marginBottom: 20
  },
  station: {
    fontSize: '1.1rem',
    paddingTop: 10,
    paddingBottom: 8
  },
  noDataAvailable: {
    paddingBottom: 8
  }
})

export const PeakBurninessPage = React.memo(function _() {
  const dispatch = useDispatch()
  const location = useLocation()
  const codesFromQuery = getStationCodesFromUrl(location.search)
  const [stationCodes, setStationCodes] = useState<number[]>(codesFromQuery)

  useEffect(() => {
    dispatch(fetchWxStations())
  }, [])

  useEffect(() => {
    if (codesFromQuery.length > 0) {
      dispatch(fetchPeakValues(codesFromQuery))
    } else {
      dispatch(resetPeakValuesResult())
    }

    setStationCodes(codesFromQuery)
  }, [location])

  return (
    <main data-testid="peak-burniness-page">
      <PageHeader title="Predictive Services Unit" productName="Peak Burniness" />
      <PageTitle title="Peak Burniness" />
      <Container>
        <WxStationDropdown stationCodes={stationCodes} onChange={setStationCodes} />
        <ErrorBoundary>
          <PeakValuesResults stationCodes={stationCodes}/>
        </ErrorBoundary>
      </Container>
    </main>
  )
})

export default React.memo(PeakBurninessPage)
