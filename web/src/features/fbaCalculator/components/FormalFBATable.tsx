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
  fireCenter: string
}

const buildAdvisoryHeader = (fireCenter: string) => (
  <h2>{fireCenter}: Fire Behaviour Advisory Summary</h2>
)

const FormalFBATable = (props: FormalFBATableProps) => {
  return (
    <TableContainer data-testid={props.testId}>
      {buildAdvisoryHeader(props.fireCenter)}
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
