import { GeneralHeader } from '@/components/GeneralHeader'
import Footer from '@/features/landingPage/components/Footer'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import ASADatePicker from '@/features/fba/components/ASADatePicker'
import RasterTypeDropdown from '@/features/sfmsInsights/components/RasterTypeDropdown'
import { FireWeatherRasterType } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { StyledFormControl } from '@/components/StyledFormControl'
import { SFMS_INSIGHTS_NAME } from '@/utils/constants'
import { getMostRecentProcessedSnowByDate } from '@/api/snow'
import { Box, Grid } from '@mui/material'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { isNull } from 'lodash'

export const SFMSInsightsPage = () => {
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const [forDate] = useState<DateTime>(DateTime.now())
  const [fwiDate, setFwiDate] = useState<DateTime>(DateTime.fromISO('2025-11-02'))
  const [rasterType, setRasterType] = useState<FireWeatherRasterType>('fwi')

  // Set date ranges for the date picker
  const historicalMinDate = DateTime.fromISO('2024-01-01')
  const historicalMaxDate = DateTime.now().plus({ days: 10 })
  const currentYearMinDate = DateTime.fromISO('2025-01-01')
  const currentYearMaxDate = DateTime.now().plus({ days: 10 })

  useEffect(() => {
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

    fetchLastProcessedSnow(forDate)
  }, [])

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
                date={fwiDate}
                updateDate={setFwiDate}
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
        </Grid>
      </Box>
      <Box sx={{ flex: 1, position: 'relative' }}>
        <SFMSMap snowDate={snowDate} fwiDate={fwiDate} rasterType={rasterType} />
      </Box>
      <Footer />
    </Box>
  )
}
