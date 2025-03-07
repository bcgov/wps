import { GeneralHeader } from '@/components/GeneralHeader'
import Footer from '@/features/landingPage/components/Footer'
import PSUMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { SFMS_INSIGHTS_NAME } from '@/utils/constants'
import Box from '@mui/material/Box'

export const SFMSInsightsPage = () => {
  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <GeneralHeader isBeta={true} spacing={1} title={SFMS_INSIGHTS_NAME} productName={SFMS_INSIGHTS_NAME} />
      <Box sx={{ flex: 1, position: 'relative' }}>
        <PSUMap />
      </Box>
      <Footer />
    </Box>
  )
}
