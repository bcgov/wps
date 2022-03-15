import { makeStyles, TableCell } from '@material-ui/core'
import { fireTableStyles, BACKGROUND_COLOR } from 'app/theme'
import { FireStarts } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import React from 'react'

export interface FireStartsCellProps {
  testId?: string
  fireStarts?: FireStarts
  areaName: string
}

const useStyles = makeStyles({
  ...fireTableStyles,
  fireStarts: {
    ...fireTableStyles.calculatedPlanningCell,
    ...BACKGROUND_COLOR
  }
})

const FireStartsCell = (props: FireStartsCellProps) => {
  const classes = useStyles()
  return (
    <TableCell
      className={classes.fireStarts}
      data-testid={`fire-starts-${props.areaName}`}
    >
      {props.fireStarts
        ? `${props.fireStarts.min_starts}-${props.fireStarts?.max_starts}`
        : ''}
    </TableCell>
  )
}

export default React.memo(FireStartsCell)
