import { Box, FormControl, Grid, styled } from '@mui/material'
import { type FireShape, RunType } from '@wps/api/fbaAPI'
import { getStations, StationSource } from '@wps/api/stationAPI'
import type { FireCentre } from '@wps/types/fireCentre'
import AboutDataPopover from '@wps/ui/AboutDataPopover'
import { ErrorBoundary } from '@wps/ui/ErrorBoundary'
import FireCentreDropdown from '@wps/ui/FireCentreDropdown'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { StyledFormControl } from '@wps/ui/StyledFormControl'
import { theme } from '@wps/ui/theme'
import { ASA_DOC_TITLE, FIRE_BEHAVIOUR_ADVISORY_NAME, PST_UTC_OFFSET } from '@wps/utils/constants'
import { selectFireCentres, selectRunDates } from 'app/rootReducer'
import type { AppDispatch } from 'app/store'
import ActualForecastControl from 'features/fba/components/ActualForecastControl'
import AdvisoryReport from 'features/fba/components/infoPanel/AdvisoryReport'
import FireZoneUnitTabs from 'features/fba/components/infoPanel/FireZoneUnitTabs'
import FBAMap from 'features/fba/components/map/FBAMap'
import { fetchFireCentreHFIFuelStats } from 'features/fba/slices/fireCentreHFIFuelStatsSlice'
import { fetchFireCentreTPIStats } from 'features/fba/slices/fireCentreTPIStatsSlice'
import { fetchProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import { fetchSFMSBounds, fetchSFMSRunDates } from 'features/fba/slices/runDatesSlice'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { isEmpty, isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchFireCentres } from '@/commonSlices/fireCentresSlice'
import { ASAAboutDataContent } from '@/features/fba/components/ASAAboutDataContent'
import ASADatePicker from '@/features/fba/components/ASADatePicker'
import Footer from '@/features/landingPage/components/Footer'

export const FireCentreFormControl = styled(FormControl)({
  margin: theme.spacing(1),
  minWidth: 280
})

const FireBehaviourAdvisoryPage: React.FunctionComponent = () => {
  const dispatch: AppDispatch = useDispatch()

  // selectors
  const { fireCentres } = useSelector(selectFireCentres)
  const { mostRecentRunDate, sfmsBounds } = useSelector(selectRunDates)

  // state
  const [fireCentre, setFireCentre] = useState<FireCentre | undefined>(undefined)
  const [selectedFireShape, setSelectedFireShape] = useState<FireShape | undefined>(undefined)
  const [zoomSource, setZoomSource] = useState<'fireCentre' | 'fireShape' | undefined>('fireCentre')
  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).hour < 13
      ? DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
      : DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).plus({ days: 1 })
  )
  const [runType, setRunType] = useState(RunType.FORECAST)
  // Set some reasonable historical min and max dates for ASA (used by the DatePicker).
  const [historicalMinDate, setHistoricalMinDate] = useState<DateTime>(
    DateTime.fromObject({ year: 2022, month: 4, day: 1 })
  )
  const [historicalMaxDate, setHistoricalMaxDate] = useState<DateTime>(DateTime.now().plus({ days: 3 }))
  // Set some reasonable min and max dates for ASA for the current year (used by forward/back arrow buttons).
  const [currentYearMinDate, setCurrentYearMinDate] = useState<DateTime>(
    DateTime.fromObject({ year: DateTime.now().year, month: 4, day: 1 })
  )
  const [currentYearMaxDate, setCurrentYearMaxDate] = useState<DateTime>(DateTime.now().plus({ days: 3 }))
  const [currentYear, setCurrentYear] = useState<number>(DateTime.now().year)

  const dateTimeComparator = (a: DateTime, b: DateTime) => a.valueOf() - b.valueOf()

  const updateDatePickerOptions = () => {
    const dates: DateTime[] = []
    const runTypeLower = runType.toLocaleLowerCase()
    if (!isNull(sfmsBounds) && !isEmpty(sfmsBounds)) {
      for (const key of Object.keys(sfmsBounds)) {
        const minValue = sfmsBounds[key]?.[runTypeLower]?.minimum
        const maxValue = sfmsBounds[key]?.[runTypeLower]?.maximum
        if (minValue && maxValue) {
          const minDate = DateTime.fromISO(minValue)
          const maxDate = DateTime.fromISO(maxValue)
          dates.push(minDate, maxDate)
        }
      }
      if (dates.length >= 2) {
        dates.sort(dateTimeComparator)
        setHistoricalMinDate(dates[0])
        setHistoricalMaxDate(dates[dates.length - 1].plus({ days: 1 }))
      }
    }
    const year = dateOfInterest.year
    const currentYearMin = sfmsBounds?.[year]?.[runTypeLower]?.minimum ?? `${currentYear}-04-01`
    const currentYearMax = sfmsBounds?.[year]?.[runTypeLower]?.maximum ?? `${currentYear}-10-31`
    setCurrentYearMinDate(DateTime.fromISO(currentYearMin))
    setCurrentYearMaxDate(DateTime.fromISO(currentYearMax))
  }

  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional — updateDatePickerOptions closes over state correctly
  useEffect(() => updateDatePickerOptions(), [currentYear, runType, sfmsBounds])

  useEffect(() => {
    const findCenter = (id: string | null): FireCentre | undefined => {
      return fireCentres.find(center => center.id.toString() === id)
    }
    setFireCentre(findCenter(localStorage.getItem('preferredFireCentre')))
  }, [fireCentres])

  useEffect(() => {
    if (fireCentre?.id) {
      localStorage.setItem('preferredFireCentre', fireCentre?.id.toString())
    }
  }, [fireCentre])

  useEffect(() => {
    if (selectedFireShape?.mof_fire_centre_name) {
      const matchingFireCentre = fireCentres.find(center => center.name === selectedFireShape.mof_fire_centre_name)

      if (matchingFireCentre) {
        setFireCentre(matchingFireCentre)
      }
    }
  }, [selectedFireShape, fireCentres])

  const updateDate = (newDate: DateTime) => {
    if (newDate !== dateOfInterest) {
      setDateOfInterest(newDate)
    }
  }

  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional — deps are captured via closure correctly
  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
  }, [runType])

  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional — fetch on mount only
  useEffect(() => {
    dispatch(fetchFireCentres())
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    dispatch(fetchSFMSBounds())
  }, [])

  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional — only re-run when date of interest changes
  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
    if (dateOfInterest.year !== currentYear) {
      setCurrentYear(dateOfInterest.year)
    }
  }, [dateOfInterest])

  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional — only re-run when fire centre or run date changes
  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (
      !isNull(mostRecentRunDate) &&
      !isNull(doiISODate) &&
      !isUndefined(mostRecentRunDate) &&
      !isUndefined(fireCentre) &&
      !isNull(fireCentre)
    ) {
      dispatch(fetchFireCentreTPIStats(fireCentre.name, runType, doiISODate, mostRecentRunDate.toString()))
      dispatch(fetchFireCentreHFIFuelStats(fireCentre.name, runType, doiISODate, mostRecentRunDate.toString()))
    }
  }, [fireCentre, mostRecentRunDate])

  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional — only re-run when most recent run date changes
  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchProvincialSummary(runType, mostRecentRunDate, doiISODate))
    }
  }, [mostRecentRunDate])

  useEffect(() => {
    document.title = ASA_DOC_TITLE
  }, [])

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <GeneralHeader isBeta={false} spacing={1} title={FIRE_BEHAVIOUR_ADVISORY_NAME} />
      <Box sx={{ paddingTop: '0.5em' }}>
        <Grid
          container
          spacing={1}
          sx={{
            alignItems: 'center'
          }}
        >
          <Grid>
            <StyledFormControl>
              <ASADatePicker
                date={dateOfInterest}
                updateDate={updateDate}
                historicalMinDate={historicalMinDate}
                historicalMaxDate={historicalMaxDate}
                currentYearMinDate={currentYearMinDate}
                currentYearMaxDate={currentYearMaxDate}
              />
            </StyledFormControl>
          </Grid>
          <ErrorBoundary>
            <Grid>
              <ActualForecastControl runType={runType} setRunType={setRunType} />
            </Grid>
          </ErrorBoundary>
          <Grid>
            <FireCentreFormControl>
              <FireCentreDropdown
                fireCentreOptions={fireCentres}
                selectedFireCentre={fireCentre}
                setSelectedFireCentre={setFireCentre}
                setSelectedFireShape={setSelectedFireShape}
                setZoomSource={setZoomSource}
              />
            </FireCentreFormControl>
          </Grid>
          <Grid sx={{ marginLeft: 'auto', paddingRight: theme.spacing(2) }}>
            <AboutDataPopover content={ASAAboutDataContent} />
          </Grid>
        </Grid>
      </Box>
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        <Box sx={{ width: 700, overflowY: 'auto' }}>
          <AdvisoryReport
            issueDate={mostRecentRunDate !== null ? DateTime.fromISO(mostRecentRunDate) : null}
            forDate={dateOfInterest}
            selectedFireCentre={fireCentre}
            selectedFireZoneUnit={selectedFireShape}
          />
          <FireZoneUnitTabs
            selectedFireZoneUnit={selectedFireShape}
            setZoomSource={setZoomSource}
            selectedFireCentre={fireCentre}
            setSelectedFireShape={setSelectedFireShape}
          />
        </Box>
        <Grid sx={{ display: 'flex', flex: 1 }}>
          <FBAMap
            forDate={dateOfInterest}
            runType={runType}
            selectedFireShape={selectedFireShape}
            selectedFireCentre={fireCentre}
            setSelectedFireShape={setSelectedFireShape}
            zoomSource={zoomSource}
            setZoomSource={setZoomSource}
          />
        </Grid>
      </Box>
      <Footer />
    </Box>
  )
}

export default React.memo(FireBehaviourAdvisoryPage)
