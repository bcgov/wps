import React from 'react'

import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { Button } from 'components'

interface Props {
  title: string
  fireCentres: Record<string, FireCentre>
  dailiesMap: Map<number, StationDaily>
  currentDay: string
  previousDay: () => void
  nextDay: () => void
  testId?: string
}

const useStyles = makeStyles({
  display: {
    paddingBottom: 12,

    '& .MuiTableCell-sizeSmall': {
      padding: '6px 12px 6px 6px'
    }
  },
  paper: {
    width: '100%'
  },
  tableContainer: {
    maxHeight: 1080,
    maxWidth: 1900,
    minWidth: 1600,
    '& .MuiTableCell-head': { fontWeight: 'bold', padding: '1px' }
  },
  fireCentre: {
    fontSize: 16,
    fontWeight: 'bold',
    backgroundColor: '#dbd9d9'
  },
  planningArea: {
    backgroundColor: '#d6faff',

    '& .MuiTableCell-sizeSmall': {
      paddingLeft: '12px'
    }
  },
  station: {
    '& .MuiTableCell-sizeSmall': {
      paddingLeft: '20px'
    }
  },
  borderless: {
    border: 'none'
  },
  controls: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'baseline'
  }
})

const DailyViewTable = (props: Props) => {
  const classes = useStyles()

  const DECIMAL_PLACES = 1

  return (
    <div className={classes.display} data-testid={props.testId}>
      <div className={classes.controls}>
        <Typography component="div" variant="subtitle2">
          {props.title}
        </Typography>
        <Button color="primary" onClick={props.previousDay}>
          Previous
        </Button>
        {props.currentDay}
        <Button color="primary" onClick={props.nextDay}>
          Next
        </Button>
      </div>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
          <Table stickyHeader aria-label="daily table view of HFI by planning area">
            <TableHead>
              <TableRow>
                <TableCell key="header-location">Location</TableCell>
                <TableCell key="header-elevation">
                  Elev.
                  <br />
                  (m)
                </TableCell>
                <TableCell key="header-fuel-type">
                  FBP
                  <br />
                  Fuel
                  <br />
                  Type
                </TableCell>
                <TableCell>Status</TableCell>
                <TableCell>
                  Temp
                  <br />
                  (&deg;C)
                </TableCell>
                <TableCell>
                  RH
                  <br />
                  (%)
                </TableCell>
                <TableCell>
                  Wind
                  <br />
                  Dir
                  <br />
                  (&deg;)
                </TableCell>
                <TableCell>
                  Wind
                  <br />
                  Speed
                  <br />
                  (km/h)
                </TableCell>
                <TableCell>
                  Precip
                  <br />
                  (mm)
                </TableCell>
                <TableCell>
                  Grass
                  <br />
                  Cure
                  <br />
                  (%)
                </TableCell>
                <TableCell>FFMC</TableCell>
                <TableCell>DMC</TableCell>
                <TableCell>DC</TableCell>
                <TableCell>ISI</TableCell>
                <TableCell>BUI</TableCell>
                <TableCell>FWI</TableCell>
                <TableCell>
                  DGR
                  <br />
                  CL
                </TableCell>
                <TableCell>
                  ROS
                  <br />
                  (m/min)
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(props.fireCentres).map(([centreName, centre]) => {
                return (
                  <React.Fragment key={`fire-centre-${centreName}`}>
                    <TableRow key={`fire-centre-${centreName}`}>
                      <TableCell className={classes.fireCentre} colSpan={26}>
                        {centre.name}
                      </TableCell>
                    </TableRow>
                    {Object.entries(centre.planning_areas)
                      .sort((a, b) => (a[1].name < b[1].name ? -1 : 1))
                      .map(([areaName, area]) => {
                        return (
                          <React.Fragment key={`zone-${areaName}`}>
                            <TableRow
                              className={classes.planningArea}
                              key={`zone-${areaName}`}
                            >
                              <TableCell className={classes.planningArea} colSpan={26}>
                                {area.name}
                              </TableCell>
                            </TableRow>
                            {Object.entries(area.stations)
                              .sort((a, b) => (a[1].code < b[1].code ? -1 : 1))
                              .map(([stationCode, station]) => {
                                const daily = props.dailiesMap.get(station.code)
                                return (
                                  <TableRow
                                    className={classes.station}
                                    key={`station-${stationCode}`}
                                  >
                                    <TableCell key={`station-${station.code}-name`}>
                                      {station.station_props.name} ({station.code})
                                    </TableCell>
                                    <TableCell key={`station-${station.code}-elevation`}>
                                      {station.station_props.elevation}
                                    </TableCell>
                                    <TableCell key={`station-${station.code}-fuel-type`}>
                                      {station.station_props.fuel_type.abbrev}
                                    </TableCell>
                                    <TableCell>{daily?.status}</TableCell>
                                    <TableCell>{daily?.temperature}</TableCell>
                                    <TableCell>{daily?.relative_humidity}</TableCell>
                                    <TableCell>
                                      {daily?.wind_direction?.toFixed(0).padStart(3, '0')}
                                    </TableCell>
                                    <TableCell>{daily?.wind_speed}</TableCell>
                                    <TableCell>{daily?.precipitation}</TableCell>
                                    <TableCell>{daily?.grass_cure_percentage}</TableCell>
                                    <TableCell>
                                      {daily?.ffmc?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell>
                                      {daily?.dmc?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell>
                                      {daily?.dc?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell>
                                      {daily?.isi?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell>
                                      {daily?.bui?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell>
                                      {daily?.ffmc?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell>{daily?.danger_class}</TableCell>
                                    <TableCell>
                                      {daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                  </TableRow>
                                )
                              })}
                          </React.Fragment>
                        )
                      })}
                  </React.Fragment>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(DailyViewTable)
