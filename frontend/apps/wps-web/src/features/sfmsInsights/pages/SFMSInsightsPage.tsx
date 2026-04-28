import { AppDispatch } from '@/app/store'
import ASADatePicker from '@/features/fba/components/ASADatePicker'
import { fetchSFMSBounds, selectEarliestSFMSBounds, selectLatestSFMSBounds } from '@/features/fba/slices/runDatesSlice'
import Footer from '@/features/landingPage/components/Footer'
import { RasterType } from '@/features/sfmsInsights/components/map/rasterConfig'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import RasterTypeDropdown from '@/features/sfmsInsights/components/RasterTypeDropdown'
import { Box, Checkbox, CircularProgress, FormControlLabel, Grid } from '@mui/material'
import { getMostRecentProcessedSnowByDate } from '@wps/api/snow'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { StyledFormControl } from '@wps/ui/StyledFormControl'
import { SFMS_INSIGHTS_NAME } from '@wps/utils/constants'
import { getDateTimeNowPST } from '@wps/utils/date'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

export const SFMSInsightsPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const latestBounds = useSelector(selectLatestSFMSBounds)
  const earliestBounds = useSelector(selectEarliestSFMSBounds)
  const sfmsBounds = useSelector((state: any) => state.runDates.sfmsBounds)
  const sfmsBoundsLoading = useSelector((state: any) => state.runDates.sfmsBoundsLoading)
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const [rasterDate, setRasterDate] = useState<DateTime | null>(getDateTimeNowPST())
  const [maxDate] = useState<DateTime>(getDateTimeNowPST().plus({ days: 10 }))
  const [minDate, setMinDate] = useState<DateTime>(
    DateTime.fromObject({ day: 1, month: 1, year: getDateTimeNowPST().year })
  )

  const [rasterType, setRasterType] = useState<RasterType>('fuel')
  const [showSnow, setShowSnow] = useState<boolean>(true)

  useEffect(() => {
    // Only fetch SFMS bounds if we haven't fetched yet (undefined) and aren't already loading
    if (sfmsBounds === undefined && !sfmsBoundsLoading) {
      dispatch(fetchSFMSBounds())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (earliestBounds?.minimum) {
      setMinDate(DateTime.fromISO(earliestBounds.minimum))
    }
  }, [earliestBounds])

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
        <Grid container spacing={1} alignItems={'center'}>
          {sfmsBoundsLoading ? (
            <Grid item>
              <StyledFormControl>
                <Box sx={{ display: 'flex', alignItems: 'center', padding: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              </StyledFormControl>
            </Grid>
          ) : (
            <Grid item>
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
          <Grid item>
            <StyledFormControl>
              <RasterTypeDropdown
                selectedRasterType={rasterType}
                setSelectedRasterType={setRasterType}
                rasterDataAvailable={!!latestBounds?.maximum}
              />
            </StyledFormControl>
          </Grid>
          <Grid item>
            <FormControlLabel
              control={<Checkbox checked={showSnow} onChange={e => setShowSnow(e.target.checked)} />}
              label={snowDate ? `Show Latest Snow: ${snowDate.toLocaleString(DateTime.DATE_MED)}` : 'Show Latest Snow'}
            />
          </Grid>
        </Grid>
      </Box>
      <Box sx={{ flex: 1, position: 'relative' }}>
        <SFMSMap snowDate={snowDate} rasterDate={rasterDate} rasterType={rasterType} showSnow={showSnow} />
      </Box>
      <Footer />
    </Box>
  )
}
