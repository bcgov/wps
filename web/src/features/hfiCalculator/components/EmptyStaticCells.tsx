import { TableCell } from '@mui/material'
import { StationPlainStylingCell } from 'features/hfiCalculator/components/StyledPlanningArea'
import WeeklyROSCell from 'features/hfiCalculator/components/WeeklyROSCell'
import React, { ReactElement } from 'react'

export interface EmptyStaticCellsProps {
  rowId: number
  isRowSelected: boolean
}

export const EmptyStaticCells = ({ rowId, isRowSelected }: EmptyStaticCellsProps): ReactElement => {
  const TableCellComponent = isRowSelected ? TableCell : StationPlainStylingCell
  return (
    <React.Fragment key={`empty-row-${rowId}`}>
      <WeeklyROSCell
        data-testid={`empty-ros-${rowId}`}
        isRowSelected={isRowSelected}
        error={true}
        isFirstDayOfPrepPeriod={true}
      />
      <TableCellComponent data-testid={`empty-hfi-${rowId}`} />
      <TableCellComponent data-testid={`empty-intensity-group-${rowId}`} />
      <TableCellComponent data-testid={`empty-fire-starts-${rowId}`} />
      <TableCellComponent data-testid={`empty-prep-level-${rowId}`} />
    </React.Fragment>
  )
}

export default React.memo(EmptyStaticCells)
