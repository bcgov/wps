import { Box, FormControl, Grid, styled } from '@mui/material'
import { GeneralHeader, ErrorBoundary } from 'components'
import React, { useEffect, useState } from 'react'
import FBAMap from 'features/fba/components/map/FBAMap'
import FireCenterDropdown from 'components/FireCenterDropdown'
import { DateTime } from 'luxon'
import { selectFireCenters, selectRunDates, selectFireShapeAreas } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import { fetchFireCenters } from 'commonSlices/fireCentersSlice'
import { theme } from 'app/theme'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource } from 'api/stationAPI'
import { FireCenter, FireShape } from 'api/fbaAPI'
import { ASA_DOC_TITLE, FIRE_BEHAVIOUR_ADVISORY_NAME, PST_UTC_OFFSET } from 'utils/constants'
import WPSDatePicker from 'components/WPSDatePicker'
import { AppDispatch } from 'app/store'
import ActualForecastControl from 'features/fba/components/ActualForecastControl'
import { fetchSFMSRunDates } from 'features/fba/slices/runDatesSlice'
import { isNull, isUndefined } from 'lodash'
import { fetchFireShapeAreas } from 'features/fba/slices/fireZoneAreasSlice'
import { StyledFormControl } from 'components/StyledFormControl'
import InfoPanel from 'features/fba/components/infoPanel/InfoPanel'
import { fetchProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import AdvisoryReport from 'features/fba/components/infoPanel/AdvisoryReport'
import FireZoneUnitTabs from 'features/fba/components/infoPanel/FireZoneUnitTabs'
import { fetchFireCentreTPIStats } from 'features/fba/slices/fireCentreTPIStatsSlice'
import AboutDataPopover from 'features/fba/components/AboutDataPopover'
import { fetchFireCentreHFIFuelStats } from 'features/fba/slices/fireCentreHFIFuelStatsSlice'

const ADVISORY_THRESHOLD = 20

export enum RunType {
  FORECAST = 'FORECAST',
  ACTUAL = 'ACTUAL'
}

export const FireCentreFormControl = styled(FormControl)({
  margin: theme.spacing(1),
  minWidth: 280
})

const FireBehaviourAdvisoryPage: React.FunctionComponent = () => {
  const dispatch: AppDispatch = useDispatch()
  const { fireCenters } = useSelector(selectFireCenters)

  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)

  const [selectedFireShape, setSelectedFireShape] = useState<FireShape | undefined>(undefined)
  const [zoomSource, setZoomSource] = useState<'fireCenter' | 'fireShape' | undefined>('fireCenter')
  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).hour < 13
      ? DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
      : DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).plus({ days: 1 })
  )
  const [runType, setRunType] = useState(RunType.FORECAST)
  const { mostRecentRunDate } = useSelector(selectRunDates)
  const { fireShapeAreas } = useSelector(selectFireShapeAreas)

  useEffect(() => {
    const findCenter = (id: string | null): FireCenter | undefined => {
      return fireCenters.find(center => center.id.toString() == id)
    }
    setFireCenter(findCenter(localStorage.getItem('preferredFireCenter')))
  }, [fireCenters])

  useEffect(() => {
    if (fireCenter?.id) {
      localStorage.setItem('preferredFireCenter', fireCenter?.id.toString())
    }
  }, [fireCenter])

  useEffect(() => {
    if (selectedFireShape?.mof_fire_centre_name) {
      const matchingFireCenter = fireCenters.find(center => center.name === selectedFireShape.mof_fire_centre_name)

      if (matchingFireCenter) {
        setFireCenter(matchingFireCenter)
      }
    }
  }, [selectedFireShape, fireCenters])

  const updateDate = (newDate: DateTime) => {
    if (newDate !== dateOfInterest) {
      setDateOfInterest(newDate)
    }
  }

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
  }, [runType]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    dispatch(fetchFireCenters())
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
  }, [dateOfInterest]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (
      !isNull(mostRecentRunDate) &&
      !isNull(doiISODate) &&
      !isUndefined(mostRecentRunDate) &&
      !isUndefined(fireCenter) &&
      !isNull(fireCenter)
    ) {
      dispatch(fetchFireCentreTPIStats(fireCenter.name, runType, doiISODate, mostRecentRunDate.toString()))
      dispatch(fetchFireCentreHFIFuelStats(fireCenter.name, runType, doiISODate, mostRecentRunDate.toString()))
    }
  }, [fireCenter, mostRecentRunDate])

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchFireShapeAreas(runType, mostRecentRunDate, doiISODate))
      dispatch(fetchProvincialSummary(runType, mostRecentRunDate, doiISODate))
    }
  }, [mostRecentRunDate]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    document.title = ASA_DOC_TITLE
  }, [])

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <GeneralHeader
        isBeta={true}
        spacing={1}
        title={FIRE_BEHAVIOUR_ADVISORY_NAME}
        productName={FIRE_BEHAVIOUR_ADVISORY_NAME}
      />
      <Box sx={{ paddingTop: '0.5em' }}>
        <Grid container spacing={1} alignItems={'center'}>
          <Grid item>
            <StyledFormControl>
              <WPSDatePicker date={dateOfInterest} updateDate={updateDate} />
            </StyledFormControl>
          </Grid>
          <ErrorBoundary>
            <Grid item>
              <ActualForecastControl runType={runType} setRunType={setRunType} />
            </Grid>
          </ErrorBoundary>
          <Grid item>
            <FireCentreFormControl>
              <FireCenterDropdown
                fireCenterOptions={fireCenters}
                selectedFireCenter={fireCenter}
                setSelectedFireCenter={setFireCenter}
                setSelectedFireShape={setSelectedFireShape}
                setZoomSource={setZoomSource}
              />
            </FireCentreFormControl>
          </Grid>
          <Grid item sx={{ marginLeft: 'auto', paddingRight: theme.spacing(2) }}>
            <AboutDataPopover advisoryThreshold={ADVISORY_THRESHOLD} />
          </Grid>
        </Grid>
      </Box>
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        <InfoPanel>
          <AdvisoryReport
            issueDate={mostRecentRunDate !== null ? DateTime.fromISO(mostRecentRunDate) : null}
            forDate={dateOfInterest}
            advisoryThreshold={ADVISORY_THRESHOLD}
            selectedFireCenter={fireCenter}
          />
          <FireZoneUnitTabs
            selectedFireZoneUnit={selectedFireShape}
            setZoomSource={setZoomSource}
            selectedFireCenter={fireCenter}
            advisoryThreshold={ADVISORY_THRESHOLD}
            setSelectedFireShape={setSelectedFireShape}
          />
        </InfoPanel>
        <Grid sx={{ display: 'flex', flex: 1 }} item>
          <FBAMap
            forDate={dateOfInterest}
            runType={runType}
            selectedFireShape={selectedFireShape}
            selectedFireCenter={fireCenter}
            advisoryThreshold={ADVISORY_THRESHOLD}
            setSelectedFireShape={setSelectedFireShape}
            fireShapeAreas={fireShapeAreas}
            zoomSource={zoomSource}
            setZoomSource={setZoomSource}
          />
        </Grid>
      </Box>
    </Box>
  )
}

export default React.memo(FireBehaviourAdvisoryPage)
