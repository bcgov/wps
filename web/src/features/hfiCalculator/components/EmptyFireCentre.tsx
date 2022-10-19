import { TableRow, TableCell } from '@mui/material'
import React from 'react'
export interface EmptyFireCentreProps {
  colSpan?: number
}
const EmptyFireCentreRow = (props: EmptyFireCentreProps): JSX.Element => (
  <React.Fragment>
    <TableRow data-testid="hfi-empty-fire-centre">
      <TableCell colSpan={props.colSpan}>To begin, select a fire centre</TableCell>
    </TableRow>
  </React.Fragment>
)

export default React.memo(EmptyFireCentreRow)
