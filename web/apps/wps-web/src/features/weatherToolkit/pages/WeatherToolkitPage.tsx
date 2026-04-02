import Footer from '@/features/landingPage/components/Footer'
import TimelineController from '@/features/weatherToolkit/components/TimelineController'
import { Box, Typography } from '@mui/material'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { WEATHER_TOOLKIT_NAME } from '@wps/utils/constants'
import { useState } from 'react'

const WeatherToolkitPage = () => {
  const [currentHour, setCurrentHour] = useState<number>(0)

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', overflow: 'hidden' }}>
      <GeneralHeader isBeta={false} spacing={0.985} title={WEATHER_TOOLKIT_NAME} />
      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        <Box sx={{ width: '320px' }}>
          <Typography variant="h4"></Typography>
        </Box>
        <Box sx={{ display: 'flex', flexGrow: 1, bgcolor: '#B9B9B9', justifyContent: 'center' }}>
          <Box sx={{ display: 'flex', height: '100%', width: '50%', bgcolor: 'orange' }}></Box>
        </Box>
      </Box>
      <TimelineController currentHour={currentHour} setCurrentHour={setCurrentHour} start={0} end={84} step={3} />
      <Footer />
    </Box>
  )
}

export default WeatherToolkitPage
