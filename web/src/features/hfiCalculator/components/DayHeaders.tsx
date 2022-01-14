import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { fireTableStyles } from 'app/theme'
import StickyCell from 'components/StickyCell'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { range } from 'lodash'
import React from 'react'
import { getPrepWeeklyDateRange } from 'utils/date'

export interface DayHeadersProps {
  testId?: string
  isoDate: string
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
  const { start } = getPrepWeeklyDateRange(props.isoDate)

  const classes = useStyles()
  return (
    <React.Fragment>
      {/* Non-day specific headers */}
      <StickyCell
        left={0}
        zIndexOffset={11}
        colSpan={2}
        className={classes.noBottomBorder}
      >
        <table>
          <tr>
            <TableCell
              className={`${classes.spaceHeader} ${classes.noBottomBorder}`}
            ></TableCell>
          </tr>
        </table>
      </StickyCell>
      <TableCell className={classes.spaceHeader}></TableCell>
      <StickyCell
        left={230}
        colSpan={2}
        zIndexOffset={11}
        className={`${classes.rightBorder} ${classes.noBottomBorder}`}
      >
        <table>
          <tr>
            <TableCell className={classes.noBottomBorder}></TableCell>
          </tr>
        </table>
      </StickyCell>
      {range(NUM_WEEK_DAYS).map(i => (
        <TableCell
          data-testid={`day-${i}`}
          colSpan={5}
          className={`${classes.dayHeader} ${i > 0 ? classes.leftBorder : undefined}`}
          key={i}
        >
          {start
            .plus({ days: i })
            .toLocaleString({ weekday: 'short', month: 'short', day: '2-digit' })}
        </TableCell>
      ))}
      <TableCell
        className={`${classes.leftBorder} ${classes.noBottomBorder}`}
      ></TableCell>
    </React.Fragment>
  )
}

export default React.memo(DayHeaders)
