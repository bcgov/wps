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
    maxWidth: 1910,
    '& .MuiTableCell-body': {
      padding: '3px'
    }
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
    fontWeight: 'bold',
    padding: '1px'
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

  const roundToOneDecimalPlace = (value: number | undefined): number | undefined => {
    if (value !== undefined) {
      return Math.round(value * 10) / 10
    }
    return undefined
  }

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
                  Elev.
                  <br />
                  (m)
                </TableCell>
                <TableCell
                  className={classes.tableHeader}
                  align="right"
                  key="header-fuel-type"
                >
                  FBP
                  <br />
                  Fuel
                  <br />
                  Type
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Status
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Temp
                  <br />
                  (°C)
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  RH
                  <br />
                  (%)
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Wind
                  <br />
                  Dir
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Wind
                  <br />
                  Speed
                  <br />
                  (km/h)
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Precip
                  <br />
                  (mm)
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Grass
                  <br />
                  Cure
                  <br />(%)
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
                  DGR
                  <br />
                  CL
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  ROS
                  <br />
                  (m/min)
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  1<br />
                  HR
                  <br />
                  Size
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Fire
                  <br />
                  Type
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Head
                  <br />
                  Fire
                  <br />
                  Intensity
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Prep
                  <br />
                  Level
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  (Mean)
                  <br />
                  Intensity
                  <br />
                  Group
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  Predicted
                  <br />
                  Fire
                  <br />
                  Starts
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  ROS
                  <br />
                  (m/min)
                  <br />
                  O1A
                </TableCell>
                <TableCell className={classes.tableHeader} align="right">
                  ROS
                  <br />
                  (m/min)
                  <br />
                  O1B
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(props.fireCentres).map(([centreName, centre]) => {
                return (
                  <React.Fragment key={`fire-centre-${centreName}`}>
                    <TableRow key={`fire-centre-${centreName}`}>
                      <TableCell className={classes.fireCentre} colSpan={26}>{centre.name}</TableCell>
                    </TableRow>
                    {Object.entries(centre.planning_areas).map(([areaName, area]) => {
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
                                <TableCell align="right">{roundToOneDecimalPlace(daily?.ffmc)}</TableCell>
                                <TableCell align="right">{roundToOneDecimalPlace(daily?.dmc)}</TableCell>
                                <TableCell align="right">{roundToOneDecimalPlace(daily?.dc)}</TableCell>
                                <TableCell align="right">{roundToOneDecimalPlace(daily?.isi)}</TableCell>
                                <TableCell align="right">{roundToOneDecimalPlace(daily?.bui)}</TableCell>
                                <TableCell align="right">{roundToOneDecimalPlace(daily?.fwi)}</TableCell>
                                <TableCell align="right">{daily?.danger_cl}</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right">TBD</TableCell>
                                <TableCell align="right" className={classes.borderless}>
                                  TBD
                                </TableCell>
                                <TableCell align="right" className={classes.borderless}>
                                  TBD
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
