import { TableCell } from '@mui/material'
import { UnSelectedTableCell } from 'features/hfiCalculator/components/StyledTableComponents'
import React from 'react'

export interface CalculatedCellProps {
  testid: string | undefined
  value: string | undefined
  error: boolean
  isRowSelected: boolean
}

const CalculatedCell = (props: CalculatedCellProps) => {
  const TableCellComponent = props.isRowSelected ? TableCell : UnSelectedTableCell

  return <TableCellComponent data-testid={props.testid}>{props.error ? '' : props.value}</TableCellComponent>
}

export default React.memo(CalculatedCell)
