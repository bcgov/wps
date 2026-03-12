import { TableCell } from '@mui/material'
import { UnSelectedTableCell } from 'features/hfiCalculator/components/StyledTableComponents'
import React from 'react'

export interface WindDirectionCellProps {
  testid?: string
  value?: number
  isRowSelected: boolean
}

export const WindDirectionCell = ({ value, isRowSelected, testid }: WindDirectionCellProps) => {
  const TableCellComponent = isRowSelected ? TableCell : UnSelectedTableCell
  return <TableCellComponent data-testid={testid}>{value?.toFixed(0).padStart(3, '0')}</TableCellComponent>
}
