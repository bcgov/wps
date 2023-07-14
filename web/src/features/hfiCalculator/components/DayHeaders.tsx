import { Table, TableBody, TableCell, TableRow, styled } from '@mui/material'
import {
  NoBottomBorderCell,
  SpaceHeaderTableCell,
  StickyCellNoBottomBorder,
  StickyCellRightBorderOnly,
  TableCellLeftBorder
} from 'features/hfiCalculator/components/StyledPlanningArea'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { calculateNumPrepDays } from 'features/hfiCalculator/util'
import { isUndefined, range } from 'lodash'
import { DateTime } from 'luxon'
import React from 'react'

export interface DayHeadersProps {
  testId?: string
  dateRange?: PrepDateRange
}

const DayHeader = styled(TableCell, {
  shouldForwardProp: prop => prop !== 'showBorder',
  name: 'dayHeader'
})<{ showBorder: boolean }>(({ showBorder }) => ({
  position: 'sticky',
  zIndex: 3,
  padding: 0,
  borderBottom: 'none',
  textAlign: 'center',
  borderLeft: showBorder ? '1px solid #c4c4c4' : undefined
}))

const DayHeaders = (props: DayHeadersProps) => {
  const start =
    isUndefined(props.dateRange) || isUndefined(props.dateRange.start_date)
      ? DateTime.now()
      : DateTime.fromISO(props.dateRange.start_date)
  const numPrepDays = calculateNumPrepDays(props.dateRange)

  return (
    <React.Fragment>
      {/* Non-day specific headers */}
      <StickyCellNoBottomBorder left={0} zIndexOffset={11} colSpan={2}>
        <Table>
          <TableBody>
            <TableRow>
              <SpaceHeaderTableCell></SpaceHeaderTableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCellNoBottomBorder>
      <SpaceHeaderTableCell></SpaceHeaderTableCell>
      <StickyCellRightBorderOnly left={227} colSpan={2} zIndexOffset={11}>
        <Table>
          <TableBody>
            <TableRow>
              <NoBottomBorderCell></NoBottomBorderCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCellRightBorderOnly>
      {range(numPrepDays).map(i => (
        <DayHeader data-testid={`day-${i}`} colSpan={5} showBorder={i > 0} key={i}>
          {start.plus({ days: i }).toLocaleString({ weekday: 'short', month: 'short', day: '2-digit' })}
        </DayHeader>
      ))}
      <TableCellLeftBorder />
    </React.Fragment>
  )
}

export default React.memo(DayHeaders)
