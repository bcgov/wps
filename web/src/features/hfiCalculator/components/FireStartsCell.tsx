import { makeStyles, TableCell } from '@material-ui/core'
import { fireTableStyles } from 'app/theme'
import React from 'react'

export interface FireStartsCellProps {
  testId?: string
  areaName: string
}

const useStyles = makeStyles({
  ...fireTableStyles,
  fireStarts: {
    ...fireTableStyles.calculatedPlanningCell,
    backgroundColor: 'rgba(40, 53, 147, 0.05)'
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
