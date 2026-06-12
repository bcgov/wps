import ASADatePicker from '@/features/fba/components/ASADatePicker'
import Footer from '@/features/landingPage/components/Footer'
import { RasterType } from '@/features/sfmsInsights/components/map/rasterConfig'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import RasterTypeDropdown from '@/features/sfmsInsights/components/RasterTypeDropdown'
import { Box, Checkbox, CircularProgress, FormControlLabel, Grid } from '@mui/material'
import { getMostRecentProcessedSnowByDate } from '@wps/api/snow'
import { getSFMSInsightsBounds, type SFMSBounds } from '@wps/api/sfmsAPI'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { StyledFormControl } from '@wps/ui/StyledFormControl'
import { SFMS_INSIGHTS_NAME } from '@wps/utils/constants'
import { getDateTimeNowPST } from '@wps/utils/date'
import { logError } from '@wps/utils/error'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'

const findActualBoundsInOrder = (
  sfmsBounds: SFMSBounds | null | undefined,
  sortFn: (a: string, b: string) => number,
  hasValue: (bounds: { minimum: string; maximum: string }) => boolean
) => {
  if (!sfmsBounds) return null

  for (const year of Object.keys(sfmsBounds).sort(sortFn)) {
    const bounds = sfmsBounds[year]?.actual
    if (bounds && hasValue(bounds)) {
      return bounds
    }
  }
  return null
}

export const SFMSInsightsPage = () => {
  const [sfmsBounds, setSfmsBounds] = useState<SFMSBounds | null | undefined>(undefined)
  const [sfmsBoundsLoading, setSfmsBoundsLoading] = useState<boolean>(false)
  const latestBounds = findActualBoundsInOrder(
    sfmsBounds,
    (a, b) => b.localeCompare(a),
    bounds => !!bounds.maximum
  )
  const earliestBounds = findActualBoundsInOrder(
    sfmsBounds,
    (a, b) => a.localeCompare(b),
    bounds => !!bounds.minimum
  )
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const [rasterDate, setRasterDate] = useState<DateTime | null>(getDateTimeNowPST())
  const [maxDate, setMaxDate] = useState<DateTime>(getDateTimeNowPST().plus({ days: 10 }))
  const [minDate, setMinDate] = useState<DateTime>(
    DateTime.fromObject({ day: 1, month: 1, year: getDateTimeNowPST().year })
  )

  const [rasterType, setRasterType] = useState<RasterType>('fwi')
  const [showSnow, setShowSnow] = useState<boolean>(true)

  useEffect(() => {
    if (sfmsBounds !== undefined || sfmsBoundsLoading) {
      return
    }

    const fetchBounds = async () => {
      try {
        setSfmsBoundsLoading(true)
        const bounds = await getSFMSInsightsBounds()
        setSfmsBounds(bounds.sfms_bounds)
      } catch (err) {
        setSfmsBounds(null)
        logError(err)
      } finally {
        setSfmsBoundsLoading(false)
      }
    }

    fetchBounds()
  }, [sfmsBounds, sfmsBoundsLoading])

  useEffect(() => {
    if (earliestBounds?.minimum) {
      setMinDate(DateTime.fromISO(earliestBounds.minimum))
    }
  }, [earliestBounds])

  useEffect(() => {
    if (latestBounds?.maximum) {
      const latestDate = DateTime.fromISO(latestBounds.maximum)
      setMaxDate(latestDate)
      setRasterDate(currentDate => (currentDate?.toISODate() === latestDate.toISODate() ? currentDate : latestDate))
    }
  }, [latestBounds])

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
              <RasterTypeDropdown
                selectedRasterType={rasterType}
                setSelectedRasterType={setRasterType}
                rasterDataAvailable={!!latestBounds?.maximum}
              />
            </StyledFormControl>
          </Grid>
          <Grid>
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
