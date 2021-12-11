import {
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@material-ui/core'
import { FBAResponse, FireBehaviourAdvisory, FireCenter } from 'api/fbaAPI'
import { ErrorBoundary } from 'components'
import FireTable from 'components/FireTable'
import { sortBy } from 'lodash'
import React from 'react'

interface FormalFBATableProps {
  testId?: string
  className: string
  fireCenter: FireCenter
  fbaResponse: FBAResponse
}

const buildAdvisoryHeader = (fireCenter: FireCenter) => (
  <h2>{fireCenter.name}: Fire Behaviour Advisory Summary</h2>
)

const FormalFBATable = (props: FormalFBATableProps) => {
  const getAdvisoryForStationCode = (code: number): FireBehaviourAdvisory | undefined => {
    const stationAdvisory = props.fbaResponse.fireBehaviourAdvisories.find(advisory => {
      advisory.station_code === code
    })
    return stationAdvisory
  }

  return (
    <TableContainer data-testid={props.testId} className={props.className}>
      {buildAdvisoryHeader(props.fireCenter)}
      <ErrorBoundary>
        <FireTable
          ariaLabel="Fire Behaviour Advisory table"
          maxWidth={800}
          maxHeight={800}
          testId={'fire-behaviour-advisory-table'}
        >
          <TableHead>
            <TableRow>
              <TableCell>Zone</TableCell>
              <TableCell>Weather Station</TableCell>
              <TableCell>Fuel Type</TableCell>
              <TableCell>Grass Cure</TableCell>
              <TableCell>Wind Speed (km/h)</TableCell>
              <TableCell>HFI</TableCell>
              <TableCell>Critical Hours 4,000 kW/m</TableCell>
              <TableCell>Critical Hours 10,000 kW/m</TableCell>
              <TableCell>ROS (m/min)</TableCell>
              <TableCell>30 min Fire Size (ha)</TableCell>
              <TableCell>60 min Fire Size (ha)</TableCell>
              <TableCell>Fire Type</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortBy(props.fireCenter.stations, 'zone').map((station, i) => {
              const advisory = getAdvisoryForStationCode(station.code)
              return (
                <TableRow key={i}>
                  <TableCell>{station.zone}</TableCell>
                  <TableCell>{`${station.name} (${station.code})`}</TableCell>
                  <TableCell>{advisory?.fuel_type}</TableCell>
                  <TableCell>{advisory?.grass_cure}</TableCell>
                  <TableCell>{advisory?.wind_speed}</TableCell>
                  <TableCell>{advisory?.hfi}</TableCell>
                  <TableCell>{advisory?.critical_hours_4000}</TableCell>
                  <TableCell>{advisory?.critical_hours_10000}</TableCell>
                  <TableCell>{advisory?.ros}</TableCell>
                  <TableCell>{advisory?.thirty_min_fire_size}</TableCell>
                  <TableCell>{advisory?.sixty_min_fire_size}</TableCell>
                  <TableCell>{advisory?.fire_type}</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </FireTable>
      </ErrorBoundary>
    </TableContainer>
  )
}

export default React.memo(FormalFBATable)
