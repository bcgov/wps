import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { range } from 'lodash'
import React from 'react'
import { getPrepStartAndEnd } from 'utils/date'

export interface DayHeadersProps {
  testid?: string | undefined
  isoDate: string
}

const useStyles = makeStyles({
  dayHeader: {
    borderLeft: '2px solid grey',
    textAlign: 'center'
  }
})
const DayHeaders = (props: DayHeadersProps) => {
  const { start } = getPrepStartAndEnd(props.isoDate + 'T00:00:00-07:00')

  const classes = useStyles()
  return (
    <React.Fragment>
      {range(5).map(i => (
        <TableCell colSpan={6} className={classes.dayHeader} key={i}>
          {start
            .plus({ days: i })
            .toJSDate()
            .toLocaleDateString('en-CA', { weekday: 'long' })}
        </TableCell>
      ))}
    </React.Fragment>
  )
}

export default React.memo(DayHeaders)
