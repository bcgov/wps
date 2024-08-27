import { Box, Tooltip } from '@mui/material'
import React from 'react'
import { getColorByFuelTypeCode } from 'features/fba/components/viz/color'
import { theme } from 'app/theme'

interface FuelDistributionProps {
  code: string
  percent: number
}

// Represents the percent contribution of the given fuel type to the overall high HFI area.
const FuelDistribution = ({ code, percent }: FuelDistributionProps) => {
  return (
    <Tooltip title={`${percent.toFixed()}%`} placement="right">
      <Box
        data-testid="fuel-distribution-box"
        sx={{ height: '75%', width: `${percent}%`, background: getColorByFuelTypeCode(code) }}
      ></Box>
    </Tooltip>
  )
}

export default React.memo(FuelDistribution)
