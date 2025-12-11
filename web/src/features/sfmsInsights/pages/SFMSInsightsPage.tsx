import { GeneralHeader } from '@/components/GeneralHeader'
import Footer from '@/features/landingPage/components/Footer'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { SFMS_INSIGHTS_NAME } from '@/utils/constants'
import { getMostRecentProcessedSnowByDate } from '@/api/snow'
import Box from '@mui/material/Box'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { isNull } from 'lodash'

export const SFMSInsightsPage = () => {
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const [forDate] = useState<DateTime>(DateTime.now())

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
      <Box sx={{ flex: 1, position: 'relative' }}>
        <SFMSMap snowDate={snowDate} fwiDate={DateTime.fromISO('2025-11-02')} />
      </Box>
      <Footer />
    </Box>
  )
}
