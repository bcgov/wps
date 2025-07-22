import { Box, Tooltip } from '@mui/material'
import React from 'react'
import { getColorByFuelTypeCode } from '@/components/profile/color'

interface FuelDistributionProps {
  code: string
  percent: number
}

// Represents the percent contribution of the given fuel type to the overall high HFI area.
const FuelDistribution = ({ code, percent }: FuelDistributionProps) => {
  return (
    <Tooltip followCursor placement="right" title={`${percent.toFixed()}%`}>
      <Box sx={{ display: 'flex', flexGrow: 1, height: '100%', alignItems: 'center' }}>
        <Box
          data-testid="fuel-distribution-box"
          sx={{ height: '75%', width: `${percent}%`, background: getColorByFuelTypeCode(code) }}
        ></Box>
      </Box>
    </Tooltip>
  )
}

export default React.memo(FuelDistribution)
