import { Table, TableBody, TableCell, TableContainer, TableRow } from '@mui/material'
import { FireCenter } from 'api/fbaAPI'
import { sortBy } from 'lodash'
import React from 'react'

interface FormalFBATableProps {
  testId?: string
  className: string
  fireCenter: FireCenter
}

const buildAdvisoryHeader = (fireCenter: FireCenter) => <h2>{fireCenter.name}: Fire Behaviour Advisory Summary</h2>

const FormalFBATable = (props: FormalFBATableProps) => {
  return (
    <TableContainer data-testid={props.testId} className={props.className}>
      {buildAdvisoryHeader(props.fireCenter)}
      <Table size="small">
        <TableBody>
          {sortBy(props.fireCenter.stations, 'zone').map((station, i) => (
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
