import { styled, TableCell } from '@mui/material'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { UNSELECTED_STATION_COLOR } from 'app/theme'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface WeeklyROSCellProps {
  daily?: StationDaily
  testId?: string
  error: boolean
  isRowSelected: boolean
  isFirstDayOfPrepPeriod: boolean
}

export const SectionSeparatorWeeklyROSCell = styled(TableCell)({
  borderLeft: '1px solid #C4C4C4'
})

export const UnSelectedWeeklyROSCell = styled(TableCell)({
  color: UNSELECTED_STATION_COLOR
})

export const UnSelectedSeparatorCell = styled(UnSelectedWeeklyROSCell)({
  borderLeft: '1px solid #C4C4C4'
})

const WeeklyROSCell = ({ daily, testId, isRowSelected, error, isFirstDayOfPrepPeriod }: WeeklyROSCellProps) => {
  const dataValue = error ? '' : daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)
  const unselectedCell = !isRowSelected && !isFirstDayOfPrepPeriod
  const selectedCell = isRowSelected && !isFirstDayOfPrepPeriod

  return (
    <>
      {isFirstDayOfPrepPeriod && <TableCell data-testid={testId}>{dataValue}</TableCell>}
      {unselectedCell && (
        <SectionSeparatorWeeklyROSCell data-testid={testId}>{dataValue}</SectionSeparatorWeeklyROSCell>
      )}
      {selectedCell && <SectionSeparatorWeeklyROSCell data-testid={testId}>{dataValue}</SectionSeparatorWeeklyROSCell>}
    </>
  )
}

export default React.memo(WeeklyROSCell)
