import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { range } from 'lodash'
import React from 'react'

const useStyles = makeStyles({
  grassCureBorder: {
    borderLeft: '2px solid grey'
  }
})
const CellHeaders = () => {
  const classes = useStyles()
  return (
    <React.Fragment>
      {range(5).map(i => (
        <React.Fragment key={i}>
          <TableCell className={classes.grassCureBorder}>
            Grass
            <br />
            Cure
            <br />
            (%)
          </TableCell>
          <TableCell>
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
