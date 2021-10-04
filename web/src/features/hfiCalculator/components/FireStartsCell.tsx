import { makeStyles, TableCell } from '@material-ui/core'
import React from 'react'

export interface FireStartsCellProps {
  testId?: string
  areaName: string
}

const useStyles = makeStyles({
  fireStarts: {
    fontWeight: 'bold',
    textAlign: 'center'
  }
})

const FireStartsCell = (props: FireStartsCellProps) => {
  const classes = useStyles()
  return (
    <TableCell
      className={classes.fireStarts}
      data-testid={`weekly-fire-starts-${props.areaName}`}
    >
      {/* using a fixed value of 0-1 Fire Starts for now */}
      0-1
    </TableCell>
  )
}

export default React.memo(FireStartsCell)
