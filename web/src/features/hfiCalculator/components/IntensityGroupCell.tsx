import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableStyles } from 'app/theme'
import React from 'react'

export interface IntensityGroupCellProps {
  testid: string | undefined
  value: number | undefined
  error: boolean
  selected: boolean
}

const useStyles = makeStyles({
  intensityGroupCell: {
    width: 30,
    textAlign: 'center'
  },
  unselectedStation: {
    ...fireTableStyles.unselectedStation,
    width: 30,
    textAlign: 'center'
  }
})

const IntensityGroupCell = (props: IntensityGroupCellProps) => {
  const classes = useStyles()

  return (
    <TableCell
      className={`${
        !props.selected && !props.error && props.value ? classes.unselectedStation : classes.intensityGroupCell
      }`}
      data-testid={props.testid}
    >
      {props.error ? '' : props.value}
    </TableCell>
  )
}

export default React.memo(IntensityGroupCell)
