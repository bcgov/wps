import { Box, Checkbox, CircularProgress, FormControlLabel, Grid } from '@mui/material'
import { RunType } from '@wps/api/runType'
import { getMostRecentProcessedSnowByDate } from '@wps/api/snow'
import AboutDataPopover from '@wps/ui/AboutDataPopover'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { StyledFormControl } from '@wps/ui/StyledFormControl'
import { SFMS_INSIGHTS_NAME } from '@wps/utils/constants'
import { getDateTimeNowPDT } from '@wps/utils/date'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import type { RootState } from '@/app/rootReducer'
import type { AppDispatch } from '@/app/store'
import ASADatePicker from '@/features/fba/components/ASADatePicker'
import Footer from '@/features/landingPage/components/Footer'
import type { RasterType } from '@/features/sfmsInsights/components/map/rasterConfig'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import RasterTypeDropdown from '@/features/sfmsInsights/components/RasterTypeDropdown'
import RunTypeDropdown from '@/features/sfmsInsights/components/RunTypeDropdown'
import { SfmsInsightsAboutDataContent } from '@/features/sfmsInsights/components/SfmsInsightsAboutDataContent'
import {
  fetchSFMSInsightsBounds,
  selectCombinedSFMSInsightsBounds,
  selectLatestSFMSInsightsBounds,
  selectSFMSInsightsBounds,
  selectSFMSInsightsBoundsLoading
} from '@/features/sfmsInsights/slices/sfmsInsightsSlice'

export const SFMSInsightsPage = () => {
  const dispatch = useDispatch<AppDispatch>()

  // state
  const [runType, setRunType] = useState<RunType>(RunType.ACTUAL)
  const [rasterType, setRasterType] = useState<RasterType>('fuel')
  const [rasterDate, setRasterDate] = useState<DateTime | null>(getDateTimeNowPDT())
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const [showSnow, setShowSnow] = useState<boolean>(true)
  const [minDate, setMinDate] = useState<DateTime>(
    DateTime.fromObject({ day: 1, month: 1, year: getDateTimeNowPDT().year })
  )
  const [maxDate, setMaxDate] = useState<DateTime>(getDateTimeNowPDT().plus({ days: 10 }))

  // selectors
  const sfmsBounds = useSelector(selectSFMSInsightsBounds)
  const sfmsBoundsLoading = useSelector(selectSFMSInsightsBoundsLoading)
  const combinedBounds = useSelector(selectCombinedSFMSInsightsBounds)
  const latestActualBounds = useSelector(selectLatestSFMSInsightsBounds)
  const latestSelectedBounds = useSelector((state: RootState) => selectLatestSFMSInsightsBounds(state, runType))

  // derived values
  const rasterDataAvailable = !!latestSelectedBounds?.maximum

  // effects
  useEffect(() => {
    if (sfmsBounds !== undefined || sfmsBoundsLoading) {
      return
    }

    dispatch(fetchSFMSInsightsBounds())
  }, [dispatch, sfmsBounds, sfmsBoundsLoading])

  // initialize from actual bounds so source changes do not move the date, while retaining today's fallback if empty
  useEffect(() => {
    if (latestActualBounds?.maximum) {
      const latestDate = DateTime.fromISO(latestActualBounds.maximum)
      setRasterDate(currentDate => (currentDate?.toISODate() === latestDate.toISODate() ? currentDate : latestDate))
    }
  }, [latestActualBounds])

  // expose the combined actual and forecast range while preserving fallback limits when either bound is unavailable
  useEffect(() => {
    if (combinedBounds?.maximum) {
      setMaxDate(DateTime.fromISO(combinedBounds.maximum))
    }
    if (combinedBounds?.minimum) {
      setMinDate(DateTime.fromISO(combinedBounds.minimum))
    }
  }, [combinedBounds])

  useEffect(() => {
    // Only fetch snow data once rasterDate is set
    if (!rasterDate) {
      return
    }

    // Query our API for the most recently processed snow coverage date <= the currently selected date.
    const fetchLastProcessedSnow = async (selectedDate: DateTime) => {
      const data = await getMostRecentProcessedSnowByDate(selectedDate)
      if (isNull(data)) {
        setSnowDate(null)
      } else {
        const newSnowDate = data.forDate
        setSnowDate(newSnowDate)
      }
    }

    fetchLastProcessedSnow(rasterDate)
  }, [rasterDate])

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <GeneralHeader isBeta={true} spacing={1} title={SFMS_INSIGHTS_NAME} />
      <Box
        sx={{
          paddingTop: '0.5em',
          borderBottomWidth: 2,
          borderBottomStyle: 'solid',
          borderBottomColor: 'secondary.main'
        }}
      >
        <Grid
          container
          spacing={1}
          sx={{
            alignItems: 'center'
          }}
        >
          {sfmsBoundsLoading ? (
            <Grid>
              <StyledFormControl>
                <Box sx={{ display: 'flex', alignItems: 'center', padding: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              </StyledFormControl>
            </Grid>
          ) : (
            <Grid>
              <StyledFormControl>
                <ASADatePicker
                  date={rasterDate}
                  updateDate={setRasterDate}
                  historicalMinDate={minDate}
                  historicalMaxDate={maxDate}
                  currentYearMinDate={minDate}
                  currentYearMaxDate={maxDate}
                />
              </StyledFormControl>
            </Grid>
          )}
          <Grid>
            <StyledFormControl>
              <RunTypeDropdown selectedRunType={runType} setSelectedRunType={setRunType} />
            </StyledFormControl>
          </Grid>
          <Grid>
            <StyledFormControl>
              <RasterTypeDropdown
                selectedRasterType={rasterType}
                setSelectedRasterType={setRasterType}
                rasterDataAvailable={rasterDataAvailable}
              />
            </StyledFormControl>
          </Grid>
          <Grid>
            <FormControlLabel
              control={<Checkbox checked={showSnow} onChange={e => setShowSnow(e.target.checked)} />}
              label={snowDate ? `Show Latest Snow: ${snowDate.toLocaleString(DateTime.DATE_MED)}` : 'Show Latest Snow'}
            />
          </Grid>
          <Grid sx={{ marginLeft: 'auto', paddingRight: 2 }}>
            <AboutDataPopover
              content={SfmsInsightsAboutDataContent}
              maxWidth={450}
              testId="sfms-insights-about-data-popover"
            />
          </Grid>
        </Grid>
      </Box>
      <Box sx={{ flex: 1, position: 'relative' }}>
        <SFMSMap
          snowDate={snowDate}
          rasterDate={rasterDate}
          rasterType={rasterType}
          runType={runType}
          showSnow={showSnow}
        />
      </Box>
      <Footer />
    </Box>
  )
}
