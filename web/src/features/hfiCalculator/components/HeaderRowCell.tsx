import { TableCell } from '@material-ui/core'
import React from 'react'

export interface HeaderRowCellProps {
  className?: string
}

export const COLSPAN = 42

const HeaderRowCell = (props: HeaderRowCellProps) => {
  return (
    <TableCell
      data-testid="header-row-cell"
      colSpan={COLSPAN}
      className={props.className}
    ></TableCell>
  )
}

export default React.memo(HeaderRowCell)
