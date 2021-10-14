import { TableCell } from '@material-ui/core'
import React from 'react'

export interface StatusCellProps {
  value: string | undefined
  className: string | undefined
}

const StatusCell = (props: StatusCellProps) => {
  return (
    <TableCell data-testid={'status-cell'} className={props.className}>
      {props.value ? props.value : 'N/A'}
    </TableCell>
  )
}

export default React.memo(StatusCell)
