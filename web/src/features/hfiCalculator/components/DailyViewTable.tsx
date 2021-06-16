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

interface Props {
  title: string
  fireCentres: Record<string, FireCentre>
  dailiesMap: Map<number, StationDaily>
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
    maxHeight: 480
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
  tableHeader: {
    fontWeight: 'bold'
  },
  borderless: {
    border: 'none'
  }
})

const DailyViewTable = (props: Props) => {
  const classes = useStyles()

  return (
    <div className={classes.display} data-testid={props.testId}>
      <Typography component="div" variant="subtitle2">
        {props.title}
      </Typography>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer>
          <Table stickyHeader aria-label="daily table view of HFI by planning area">
            <TableHead>
              <TableRow>
                {/* TableHead and TableRow don't apply classes.tableHeader styling - has to be assigned to TableCell */}
                <TableCell
                  className={classes.tableHeader}
                  align="right"
                  key="header-location"
                >
                  Location
                </TableCell>
                <TableCell
                  className={classes.tableHeader}
                  align="right"
                  key="header-elevation"
                >
                  Elev. (m)
                </TableCell>
                <TableCell
                  className={classes.tableHeader}
                  align="right"
                  key="header-fuel-type"
                >
                  FBP Fuel Type
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Status
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Temp
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  RH
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Wind Dir
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Wind Speed
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Precip
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Grass Cure %
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  FFMC
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  DMC
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  DC
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  ISI
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  BUI
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  FWI
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  DGR CL
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  FBP Fuel Type
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  ROS (m/min)
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  1 HR Size
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Fire Type
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Head Fire Intensity
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Prep Level
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  (Mean) Intensity Group
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Predicted Fire Starts
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  ROS (m/min)
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell align="right">01A</TableCell>
                          <TableCell align="right">01B</TableCell>
                        </TableRow>
                      </TableHead>
                    </Table>
                  </TableContainer>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(props.fireCentres).map(([centreName, centre]) => {
                return (
                  <React.Fragment key={`fire-centre-${centreName}`}>
                    <TableRow key={`fire-centre-${centreName}`}>
                      <TableCell colSpan={3} className={classes.fireCentre}>
                        {centre.name}
                      </TableCell>
                    </TableRow>
                    {Object.entries(centre.planning_areas).map(([areaName, area]) => {
                      return (
                        <React.Fragment key={`zone-${areaName}`}>
                          <TableRow
                            className={classes.planningArea}
                            key={`zone-${areaName}`}
                          >
                            <TableCell className={classes.planningArea} colSpan={3}>
                              {area.name}
                            </TableCell>
                          </TableRow>
                          {Object.entries(area.stations).map(([stationCode, station]) => {
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
                                <TableCell align="right">{daily?.status}</TableCell>
                                <TableCell align="right">{daily?.temperature}</TableCell>
                                <TableCell align="right">
                                  {daily?.relative_humidity}
                                </TableCell>
                                <TableCell align="right">
                                  {daily?.wind_direction}
                                </TableCell>
                                <TableCell align="right">{daily?.wind_speed}</TableCell>
                                <TableCell align="right">
                                  {daily?.precipitation}
                                </TableCell>
                                <TableCell align="right">
                                  {daily?.grass_cure_percentage}
                                </TableCell>
                                <TableCell align="right">{daily?.ffmc}</TableCell>
                                <TableCell align="right">{daily?.dmc}</TableCell>
                                <TableCell align="right">{daily?.dc}</TableCell>
                                <TableCell align="right">{daily?.isi}</TableCell>
                                <TableCell align="right">{daily?.bui}</TableCell>
                                <TableCell align="right">{daily?.fwi}</TableCell>
                                <TableCell align="right">{daily?.danger_cl}</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">
                                  <TableContainer>
                                    <Table>
                                      <TableRow>
                                        <TableCell
                                          align="right"
                                          className={classes.borderless}
                                        >
                                          TBD
                                        </TableCell>
                                        <TableCell
                                          align="right"
                                          className={classes.borderless}
                                        >
                                          TBD
                                        </TableCell>
                                      </TableRow>
                                    </Table>
                                  </TableContainer>
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
