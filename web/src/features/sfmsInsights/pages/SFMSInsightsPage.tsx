import { GeneralHeader } from '@/components/GeneralHeader'
import Footer from '@/features/landingPage/components/Footer'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import ASADatePicker from '@/features/fba/components/ASADatePicker'
import RasterTypeDropdown from '@/features/sfmsInsights/components/RasterTypeDropdown'
import { StyledFormControl } from '@/components/StyledFormControl'
import { SFMS_INSIGHTS_NAME } from '@/utils/constants'
import { getMostRecentProcessedSnowByDate } from '@/api/snow'
import { fetchSFMSBounds } from '@/features/fba/slices/runDatesSlice'
import { Box, Checkbox, FormControlLabel, Grid } from '@mui/material'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { isNull } from 'lodash'
import { RasterType } from '@/features/sfmsInsights/components/map/rasterConfig'
import { getDateTimeNowPST } from '@/utils/date'
import { AppDispatch } from '@/app/store'
import { RootState } from '@/app/rootReducer'

export const SFMSInsightsPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const sfmsBounds = useSelector((state: RootState) => state.runDates.sfmsBounds)
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const [rasterDate, setRasterDate] = useState<DateTime | null>(null)
  const [rasterType, setRasterType] = useState<RasterType>('fwi')
  const [showSnow, setShowSnow] = useState<boolean>(true)

  // Calculate max date from SFMS bounds
  const currentYear = getDateTimeNowPST().year.toString()
  const forecastBounds = sfmsBounds?.[currentYear]?.forecast
  const maxDate = forecastBounds?.maximum
    ? DateTime.fromISO(forecastBounds.maximum)
    : getDateTimeNowPST().plus({ days: 10 })

  // Set date ranges for the date picker - disable dates after maxDate
  const historicalMinDate = DateTime.fromISO('2024-01-01')
  const historicalMaxDate = maxDate
  const currentYearMinDate = DateTime.fromISO('2025-01-01')
  const currentYearMaxDate = maxDate

  useEffect(() => {
    // Fetch SFMS bounds on mount
    dispatch(fetchSFMSBounds())
  }, [dispatch])

  useEffect(() => {
    // Set rasterDate once SFMS bounds are loaded
    if (sfmsBounds) {
      if (forecastBounds?.maximum) {
        setRasterDate(maxDate)
      } else {
        // Fallback to current date if no bounds for current year
        setRasterDate(getDateTimeNowPST())
      }
    }
  }, [sfmsBounds, forecastBounds, maxDate])

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

  if (!rasterDate) {
    return (
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <GeneralHeader isBeta={true} spacing={1} title={SFMS_INSIGHTS_NAME} />
        <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</Box>
        <Footer />
      </Box>
    )
  }

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
          <Grid item>
            <StyledFormControl>
              <ASADatePicker
                date={rasterDate}
                updateDate={setRasterDate}
                historicalMinDate={historicalMinDate}
                historicalMaxDate={historicalMaxDate}
                currentYearMinDate={currentYearMinDate}
                currentYearMaxDate={currentYearMaxDate}
              />
            </StyledFormControl>
          </Grid>
          <Grid item>
            <StyledFormControl>
              <RasterTypeDropdown selectedRasterType={rasterType} setSelectedRasterType={setRasterType} />
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
