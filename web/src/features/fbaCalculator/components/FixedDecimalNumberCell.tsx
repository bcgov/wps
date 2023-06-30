import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import React from 'react'

const PREFIX = 'FixedDecimalNumberCell'

const classes = {
  dataRow: `${PREFIX}-dataRow`
}

const StyledTableCell = styled(TableCell)({
  height: '40px',
  paddingLeft: '8px',
  paddingRight: '8px'
})

interface FixedDecimalNumberCellProps {
  value: number | undefined
  testId?: string
  className?: string
}

const DECIMAL_PLACES = 1

const FixedDecimalNumberCell = (props: FixedDecimalNumberCellProps) => {
  return (
    <StyledTableCell data-testid={props.testId} className={props.className ? props.className : classes.dataRow}>
      {props.value?.toFixed(DECIMAL_PLACES)}
    </StyledTableCell>
  )
}

export default React.memo(FixedDecimalNumberCell)
