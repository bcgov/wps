import { TableCell } from '@mui/material'
import WeeklyROSCell from 'features/hfiCalculator/components/WeeklyROSCell'
import React, { ReactElement } from 'react'

export interface EmptyStaticCellsProps {
  rowId: number
  isRowSelected: boolean
  classNameForRow: string | undefined
}

export const EmptyStaticCells = ({ rowId, isRowSelected, classNameForRow }: EmptyStaticCellsProps): ReactElement => {
  return (
    <React.Fragment key={`empty-row-${rowId}`}>
      <WeeklyROSCell
        data-testid={`empty-ros-${rowId}`}
        isRowSelected={isRowSelected}
        error={true}
        isFirstDayOfPrepPeriod={true}
      />
      <TableCell data-testid={`empty-hfi-${rowId}`} className={classNameForRow} />
      <TableCell data-testid={`empty-intensity-group-${rowId}`} className={classNameForRow} />
      <TableCell data-testid={`empty-fire-starts-${rowId}`} className={classNameForRow} />
      <TableCell data-testid={`empty-prep-level-${rowId}`} className={classNameForRow} />
    </React.Fragment>
  )
}

export default React.memo(EmptyStaticCells)
