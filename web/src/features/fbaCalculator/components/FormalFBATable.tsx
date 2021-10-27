import { Table, TableBody, TableCell, TableContainer, TableRow } from '@material-ui/core'
import { GeoJsonStation, DetailedGeoJsonStation } from 'api/stationAPI'
import React from 'react'

interface FormalFBATableProps {
  testId?: string
  fireCenter: string
  stations: GeoJsonStation[] | DetailedGeoJsonStation[]
}

const buildAdvisoryHeader = (fireCenter: string) => (
  <h2>{fireCenter}: Fire Behaviour Advisory Summary</h2>
)

const FormalFBATable = (props: FormalFBATableProps) => {
  return (
    <TableContainer data-testid={props.testId}>
      {buildAdvisoryHeader(props.fireCenter)}
      <Table>
        <TableBody>
          {props.stations.map((station, i) => (
            <TableRow key={i}>
              <TableCell>
                {station.properties.name} ({station.properties.code})
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(FormalFBATable)
