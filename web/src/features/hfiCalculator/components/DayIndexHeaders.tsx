import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { fireTableStyles } from 'app/theme'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { range } from 'lodash'
import React from 'react'

const useStyles = makeStyles({
  ...fireTableStyles
})
const DayIndexHeaders = () => {
  const classes = useStyles()
  return (
    <React.Fragment>
      {range(NUM_WEEK_DAYS).map(i => (
        <React.Fragment key={i}>
          <TableCell
            data-testid={`ros-header-${i}`}
            className={classes.sectionSeparatorBorder}
          >
            ROS
            <br />
            (m/min)
          </TableCell>
          <TableCell data-testid={`hfi-header-${i}`}>HFI</TableCell>
          <TableCell data-testid={`fig-header-${i}`}>
            M /
            <br />
            FIG
          </TableCell>
          <TableCell data-testid={`fire-starts-header-${i}`}>
            Fire
            <br />
            Starts
          </TableCell>
          <TableCell data-testid={`prep-level-header-${i}`}>
            Prep
            <br />
            Level
          </TableCell>
        </React.Fragment>
      ))}
    </React.Fragment>
  )
}

export default React.memo(DayIndexHeaders)
