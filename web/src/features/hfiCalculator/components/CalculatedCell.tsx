import { TableCell } from '@mui/material'
import React from 'react'

export interface CalculatedCellProps {
  testid: string | undefined
  value: string | undefined
  error: boolean
  className: string | undefined
}

const CalculatedCell = (props: CalculatedCellProps) => {
  return (
    <TableCell data-testid={props.testid} className={props.className}>
      {props.error ? '' : props.value}
    </TableCell>
  )
}

export default React.memo(CalculatedCell)
