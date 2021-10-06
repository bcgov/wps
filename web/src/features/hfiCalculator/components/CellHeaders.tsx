import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { range } from 'lodash'
import React from 'react'

const useStyles = makeStyles({
  rosBorder: {
    borderLeft: '1px solid #C4C4C4'
  }
})
const CellHeaders = () => {
  const classes = useStyles()
  return (
    <React.Fragment>
      {range(NUM_WEEK_DAYS).map(i => (
        <React.Fragment key={i}>
          <TableCell className={classes.rosBorder}>
            ROS
            <br />
            (m/min)
          </TableCell>
          <TableCell>HFI</TableCell>
          <TableCell>
            M /
            <br />
            FIG
          </TableCell>
          <TableCell>
            Fire
            <br />
            Starts
          </TableCell>
          <TableCell>
            Prep
            <br />
            Level
          </TableCell>
        </React.Fragment>
      ))}
    </React.Fragment>
  )
}

export default React.memo(CellHeaders)
