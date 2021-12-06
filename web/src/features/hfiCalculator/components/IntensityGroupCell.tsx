import { makeStyles, TableCell } from '@material-ui/core'
import { fireTableStyles } from 'app/theme'
import { intensityGroupColours } from 'features/hfiCalculator/components/meanIntensity'
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
        !props.selected && !props.error && props.value
          ? classes.unselectedStation
          : classes.intensityGroupCell
      }`}
      data-testid={props.testid}
    >
      {props.error ? '' : props.value}
    </TableCell>
  )
}

export default React.memo(IntensityGroupCell)
