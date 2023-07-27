import { styled } from '@mui/material'
import { BACKGROUND_COLOR } from 'app/theme'
import { CalculatedPlanningCell } from 'features/hfiCalculator/components/StyledPlanningAreaComponents'
import { FireStartRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import React from 'react'

export interface FireStartsCellProps {
  testId?: string
  fireStarts?: FireStartRange
  areaName: string
}

const StyledFireStartsCell = styled(CalculatedPlanningCell)({
  ...BACKGROUND_COLOR
})

const FireStartsCell = (props: FireStartsCellProps) => {
  return (
    <StyledFireStartsCell data-testid={`fire-starts-${props.areaName}`}>
      {props.fireStarts ? props.fireStarts.label : ''}
    </StyledFireStartsCell>
  )
}

export default React.memo(FireStartsCell)
