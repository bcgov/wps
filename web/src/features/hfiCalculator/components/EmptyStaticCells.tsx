import { TableCell } from '@material-ui/core'
import React, { ReactElement } from 'react'

export interface EmptyStaticCellsProps {
  rowId: number
  classNameForRow: string | undefined
}

export const EmptyStaticCells = ({
  rowId,
  classNameForRow
}: EmptyStaticCellsProps): ReactElement => {
  return (
    <React.Fragment key={`empty-row-${rowId}`}>
      <TableCell data-testid={`empty-ros-${rowId}`} className={classNameForRow} />
      <TableCell data-testid={`empty-hfi-${rowId}`} className={classNameForRow} />
      <TableCell
        data-testid={`empty-intensity-group-${rowId}`}
        className={classNameForRow}
      />
      <TableCell data-testid={`empty-fire-starts-${rowId}`} className={classNameForRow} />
      <TableCell data-testid={`empty-prep-level-${rowId}`} className={classNameForRow} />
    </React.Fragment>
  )
}

export default React.memo(EmptyStaticCells)
