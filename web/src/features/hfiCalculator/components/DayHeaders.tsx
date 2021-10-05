import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { range } from 'lodash'
import React from 'react'
import { getPrepWeeklyDateRange } from 'utils/date'

export interface DayHeadersProps {
  testId?: string
  isoDate: string
}

const useStyles = makeStyles({
  dayHeader: {
    borderLeft: '2px solid grey',
    textAlign: 'center'
  }
})
const DayHeaders = (props: DayHeadersProps) => {
  const { start } = getPrepWeeklyDateRange(props.isoDate + 'T00:00:00-07:00')

  const classes = useStyles()
  return (
    <React.Fragment>
      {range(5).map(i => (
        <TableCell colSpan={6} className={classes.dayHeader} key={i}>
          {start
            .plus({ days: i })
            .toLocaleString({ weekday: 'short', month: 'short', day: '2-digit' })}
        </TableCell>
      ))}
    </React.Fragment>
  )
}

export default React.memo(DayHeaders)
