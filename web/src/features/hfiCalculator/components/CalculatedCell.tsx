import { TableCell } from '@material-ui/core'
import React from 'react'

export interface CalculatedCellProps {
  testid: string | undefined
  value: string | undefined
  error: boolean
}

const CalculatedCell = (props: CalculatedCellProps) => {
  return (
    <TableCell data-testid={props.testid}>{props.error ? '' : props.value}</TableCell>
  )
}

export default React.memo(CalculatedCell)
