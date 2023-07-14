import { Table, TableBody, TableCell, TableRow } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableStyles } from 'app/theme'
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

const useStyles = makeStyles({
  ...fireTableStyles,
  dayHeader: {
    position: 'sticky',
    zIndex: 3,
    padding: 0,
    borderBottom: 'none',
    textAlign: 'center'
  }
})
const DayHeaders = (props: DayHeadersProps) => {
  const start =
    isUndefined(props.dateRange) || isUndefined(props.dateRange.start_date)
      ? DateTime.now()
      : DateTime.fromISO(props.dateRange.start_date)
  const numPrepDays = calculateNumPrepDays(props.dateRange)

  const classes = useStyles()
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
        <TableCell
          data-testid={`day-${i}`}
          colSpan={5}
          className={`${classes.dayHeader} ${i > 0 ? classes.leftBorder : undefined}`}
          key={i}
        >
          {start.plus({ days: i }).toLocaleString({ weekday: 'short', month: 'short', day: '2-digit' })}
        </TableCell>
      ))}
      <TableCellLeftBorder />
    </React.Fragment>
  )
}

export default React.memo(DayHeaders)
