import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@material-ui/core'
import React from 'react'

interface FormalFBATableProps {
  testId?: string
}

const FormalFBATable = (props: FormalFBATableProps) => {
  return (
    <TableContainer data-testid={props.testId}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>TODO Header</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>TODO Value</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(FormalFBATable)
