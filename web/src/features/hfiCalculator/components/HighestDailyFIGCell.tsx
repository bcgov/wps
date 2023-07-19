import { styled, TableCell } from '@mui/material'
import { UNSELECTED_STATION_COLOR } from 'app/theme'
import React from 'react'

export interface WeeklyROSCellProps {
  testId?: string
  isRowSelected: boolean
}

export const SectionSeparatedTableCell = styled(TableCell)({
  borderLeft: '1px solid #C4C4C4'
})

export const UnSelectedTableCell = styled(TableCell)({
  color: UNSELECTED_STATION_COLOR
})

const HighestDailyFIGCell = ({ testId, isRowSelected }: WeeklyROSCellProps) => {
  return isRowSelected ? (
    <SectionSeparatedTableCell data-testid={testId} />
  ) : (
    <UnSelectedTableCell data-testid={testId} />
  )
}

export default React.memo(HighestDailyFIGCell)
