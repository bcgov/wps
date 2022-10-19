import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableStyles, BACKGROUND_COLOR } from 'app/theme'
import { FireStartRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import React from 'react'

export interface FireStartsCellProps {
  testId?: string
  fireStarts?: FireStartRange
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
    <TableCell className={classes.fireStarts} data-testid={`fire-starts-${props.areaName}`}>
      {props.fireStarts ? props.fireStarts.label : ''}
    </TableCell>
  )
}

export default React.memo(FireStartsCell)
