import { Table, TableBody, TableCell, TableContainer, TableRow } from '@material-ui/core'
import { FireCenter } from 'api/fbaAPI'
import React from 'react'

interface FormalFBATableProps {
  testId?: string
  fireCenter: FireCenter
}

const buildAdvisoryHeader = (fireCenter: FireCenter) => (
  <h2>{fireCenter.name}: Fire Behaviour Advisory Summary</h2>
)

const FormalFBATable = (props: FormalFBATableProps) => {
  return (
    <TableContainer data-testid={props.testId}>
      {buildAdvisoryHeader(props.fireCenter)}
      <Table>
        <TableBody>
          {props.fireCenter.stations.map((station, i) => (
            <TableRow key={i}>
              <TableCell>
                {station.zone ? `${station.zone},` : ''} {station.name} ({station.code})
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(FormalFBATable)
