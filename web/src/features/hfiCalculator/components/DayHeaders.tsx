import { Table, TableBody, TableCell, TableRow } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableStyles } from 'app/theme'
import StickyCell from 'components/StickyCell'
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
      <StickyCell left={0} zIndexOffset={11} colSpan={2} className={classes.noBottomBorder}>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell className={`${classes.spaceHeader} ${classes.noBottomBorder}`}></TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <TableCell className={classes.spaceHeader}></TableCell>
      <StickyCell
        left={227}
        colSpan={2}
        zIndexOffset={11}
        className={`${classes.rightBorder} ${classes.noBottomBorder}`}
      >
        <Table>
          <TableBody>
            <TableRow>
              <TableCell className={classes.noBottomBorder}></TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
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
      <TableCell className={`${classes.leftBorder} ${classes.noBottomBorder}`}></TableCell>
    </React.Fragment>
  )
}

export default React.memo(DayHeaders)
