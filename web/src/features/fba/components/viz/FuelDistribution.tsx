import { Box } from '@mui/material'
import React from 'react'
import { getColorByFuelTypeCode } from 'features/fba/components/viz/color'

interface FuelDistributionProps {
  code: string
  percent: number
}

// Represents the percent contribution of the given fuel type to the overall high HFI area.
const FuelDistribution = ({ code, percent }: FuelDistributionProps) => {
  return (
    <Box
      data-testid="fuel-distribution-box"
      sx={{ height: '75%', width: `${percent}%`, background: getColorByFuelTypeCode(code) }}
    />
  )
}

export default React.memo(FuelDistribution)
