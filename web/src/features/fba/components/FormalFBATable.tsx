import {
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@material-ui/core'
import { makeStyles } from '@material-ui/styles'
import { FBAResponse, FireBehaviourAdvisory, FireCenter } from 'api/fbaAPI'
import { ErrorBoundary } from 'components'
import FireTable from 'components/FireTable'
import FireTypeTooltip from 'features/fbaCalculator/components/FireTypeTooltip'
import TableHeader from 'features/fbaCalculator/components/TableHeader'
import { isUndefined, sortBy } from 'lodash'
import React from 'react'

interface FormalFBATableProps {
  testId?: string
  className: string
  fireCenter: FireCenter
  fbaResponse: FBAResponse | undefined
}

const useStyles = makeStyles({
  headerCell: {
    zIndex: 1103,
    paddingRight: '30px',
    width: '110px'
  }
})

const buildAdvisoryHeader = (fireCenter: FireCenter) => (
  <h2>{fireCenter.name}: Fire Behaviour Advisory Summary</h2>
)

const FormalFBATable = (props: FormalFBATableProps) => {
  const classes = useStyles()

  const getAdvisoryForStationCode = (code: number): FireBehaviourAdvisory | undefined => {
    if (
      !isUndefined(props.fbaResponse) &&
      !isUndefined(props.fbaResponse.fireBehaviourAdvisories)
    ) {
      return props.fbaResponse.fireBehaviourAdvisories.find(
        advisory => advisory.station_code == code
      )
    }
    return undefined
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
              <TableCell className={classes.headerCell}>
                <TableHeader text={'Zone'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'Weather Station'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'Fuel Type'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'Grass Cure'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'Wind Speed (km/h)'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'HFI'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'Critical Hours 4,000 kW/m'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'Critical Hours 10,000 kW/m'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'ROS (m/min)'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'30 min Fire Size (ha)'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <TableHeader text={'60 min Fire Size (ha)'} />
              </TableCell>
              <TableCell className={classes.headerCell}>
                <FireTypeTooltip />
                <TableHeader text={'Fire Type'} />
              </TableCell>
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
                  <TableCell>{advisory?.wind_speed?.toFixed(0)}</TableCell>
                  <TableCell>{advisory?.head_fire_intensity?.toFixed(0)}</TableCell>
                  <TableCell>{advisory?.critical_hours_hfi_4000}</TableCell>
                  <TableCell>{advisory?.critical_hours_hfi_10000}</TableCell>
                  <TableCell>{advisory?.rate_of_spread?.toFixed(1)}</TableCell>
                  <TableCell>{advisory?.thirty_minute_fire_size?.toFixed(1)}</TableCell>
                  <TableCell>{advisory?.sixty_minute_fire_size?.toFixed(1)}</TableCell>
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
