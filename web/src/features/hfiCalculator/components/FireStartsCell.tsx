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
  const value = props.fireStarts
    ? props.fireStarts.max_starts > 15
      ? `${props.fireStarts.min_starts}+`
      : `${props.fireStarts.min_starts}-${props.fireStarts.max_starts}`
    : ''
  const classes = useStyles()
  return (
    <TableCell
      className={classes.fireStarts}
      data-testid={`fire-starts-${props.areaName}`}
    >
      {value}
    </TableCell>
  )
}

export default React.memo(FireStartsCell)
