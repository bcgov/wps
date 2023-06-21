import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import { fireTableStyles } from 'app/theme'
import React from 'react'

const PREFIX = 'IntensityGroupCell'

const classes = {
  intensityGroupCell: `${PREFIX}-intensityGroupCell`,
  unselectedStation: `${PREFIX}-unselectedStation`
}

const StyledTableCell = styled(TableCell)({
  [`& .${classes.intensityGroupCell}`]: {
    width: 30,
    textAlign: 'center'
  },
  [`& .${classes.unselectedStation}`]: {
    ...fireTableStyles.unselectedStation,
    width: 30,
    textAlign: 'center'
  }
})

export interface IntensityGroupCellProps {
  testid: string | undefined
  value: number | undefined
  error: boolean
  selected: boolean
}

const IntensityGroupCell = (props: IntensityGroupCellProps) => {
  return (
    <StyledTableCell
      className={`${
        !props.selected && !props.error && props.value ? classes.unselectedStation : classes.intensityGroupCell
      }`}
      data-testid={props.testid}
    >
      {props.error ? '' : props.value}
    </StyledTableCell>
  )
}

export default React.memo(IntensityGroupCell)
