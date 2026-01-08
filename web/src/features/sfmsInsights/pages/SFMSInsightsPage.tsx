import { GeneralHeader } from '@/components/GeneralHeader'
import Footer from '@/features/landingPage/components/Footer'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import ASADatePicker from '@/features/fba/components/ASADatePicker'
import RasterTypeDropdown from '@/features/sfmsInsights/components/RasterTypeDropdown'
import { StyledFormControl } from '@/components/StyledFormControl'
import { SFMS_INSIGHTS_NAME } from '@/utils/constants'
import { getMostRecentProcessedSnowByDate } from '@/api/snow'
import { fetchSFMSBounds, selectLatestSFMSBounds, selectEarliestSFMSBounds } from '@/features/fba/slices/runDatesSlice'
import { Box, Checkbox, FormControlLabel, Grid } from '@mui/material'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { isNull } from 'lodash'
import { RasterType } from '@/features/sfmsInsights/components/map/rasterConfig'
import { getDateTimeNowPST } from '@/utils/date'
import { AppDispatch } from '@/app/store'

export const SFMSInsightsPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const latestBounds = useSelector(selectLatestSFMSBounds)
  const earliestBounds = useSelector(selectEarliestSFMSBounds)
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const [rasterDate, setRasterDate] = useState<DateTime | null>(null)
  const [maxDate, setMaxDate] = useState<DateTime>(getDateTimeNowPST().plus({ days: 10 }))
  const [minDate, setMinDate] = useState<DateTime>(
    DateTime.fromObject({ day: 1, month: 1, year: getDateTimeNowPST().year })
  )

  const [rasterType, setRasterType] = useState<RasterType>('fwi')
  const [showSnow, setShowSnow] = useState<boolean>(true)

  useEffect(() => {
    // Fetch SFMS bounds on mount
    dispatch(fetchSFMSBounds())
  }, [dispatch])

  useEffect(() => {
    // Set rasterDate once SFMS bounds are loaded
    if (latestBounds?.maximum) {
      const latestBoundsDateTime = DateTime.fromISO(latestBounds.maximum)
      setRasterDate(latestBoundsDateTime)
      setMaxDate(latestBoundsDateTime)
    } else {
      // No raster data available, ensure fuel is selected
      setRasterType('fuel')
    }
    if (earliestBounds?.minimum) {
      setMinDate(DateTime.fromISO(earliestBounds.minimum))
    }
  }, [latestBounds, earliestBounds])

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
          <Grid item>
            <StyledFormControl>
              <RasterTypeDropdown
                selectedRasterType={rasterType}
                setSelectedRasterType={setRasterType}
                rasterDataAvailable={!!rasterDate}
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
        {rasterDate && (
          <SFMSMap snowDate={snowDate} rasterDate={rasterDate} rasterType={rasterType} showSnow={showSnow} />
        )}
      </Box>
      <Footer />
    </Box>
  )
}
