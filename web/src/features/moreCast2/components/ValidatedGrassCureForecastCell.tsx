import React from 'react'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import ValidatedCell from '@/features/moreCast2/components/ValidatedCell'
import { Box } from '@mui/material'

interface ValidatedGrassCureForecastCellProps {
  disabled: boolean
  label: string
  value: Pick<GridRenderCellParams, 'formattedValue'>
  validator?: (value: string) => string
}

const ValidatedGrassCureForecastCell = ({ disabled, label, value, validator }: ValidatedGrassCureForecastCellProps) => {
  const error = validator ? validator(value as string) : ''
  return (
    <Box data-testid="validated-gc-forecast-cell">
      <ValidatedCell disabled={disabled} label={label} error={error !== ''} invalid={error} value={value} />
    </Box>
  )
}

export default React.memo(ValidatedGrassCureForecastCell)
