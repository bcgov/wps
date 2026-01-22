import React from 'react'
import { Box, Button } from '@mui/material'

const SpotRequest: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
      <Button
        variant="contained"
        href="https://submit.digital.gov.bc.ca/app/form/submit?f=e5a6ec9b-ead7-4f5b-bdcb-88f53caae53d"
        target="_blank"
        rel="noopener noreferrer"
      >
        Request a Spot Forecast
      </Button>
    </Box>
  )
}

export default SpotRequest
