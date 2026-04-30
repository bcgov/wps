import { TableCell } from '@mui/material'
import { UnSelectedTableCell } from 'features/hfiCalculator/components/StyledTableComponents'
import React from 'react'

export interface DangerClassCellProps {
  testid?: string
  value?: number
  isRowSelected: boolean
}

export const DangerClassCell = ({ value, isRowSelected, testid }: DangerClassCellProps) => {
  const TableCellComponent = isRowSelected ? TableCell : UnSelectedTableCell
  return <TableCellComponent data-testid={testid}>{value}</TableCellComponent>
}
