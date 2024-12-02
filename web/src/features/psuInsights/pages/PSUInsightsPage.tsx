import { GeneralHeader } from '@/components/GeneralHeader'
import PSUMap from '@/features/psuInsights/components/map/PSUMap'
import { PSU_INSIGHTS_NAME } from '@/utils/constants'
import Box from '@mui/material/Box'

export const PSUInsightsPage = () => {
  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <GeneralHeader isBeta={true} spacing={1} title={PSU_INSIGHTS_NAME} productName={PSU_INSIGHTS_NAME} />
      <Box sx={{ flex: 1, position: 'relative' }}>
        <PSUMap />
      </Box>
    </Box>
  )
}
