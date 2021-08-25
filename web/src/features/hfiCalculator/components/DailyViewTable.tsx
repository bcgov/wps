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
    },

    '& .MuiTableCell-body': {
      padding: '8px'
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
  },
  intensityGroupOutline1: {
    border: '2px solid #D6FCA4',
    borderRadius: '4px'
  },
  intensityGroupOutline2: {
    border: '2px solid #73FBFD',
    borderRadius: '4px'
  },
  intensityGroupOutline3: {
    border: '2px solid #FFFEA6',
    borderRadius: '4px'
  },
  intensityGroupOutline4: {
    border: '2px solid #F7CDA0',
    borderRadius: '4px'
  },
  intensityGroupOutline5: {
    border: '2px solid #EC5D57',
    borderRadius: '4px'
  },
  intensityGroupSolid1: {
    background: '#D6FCA4',
    fontWeight: 'bold'
  },
  intensityGroupSolid2: {
    background: '#73FBFD',
    fontWeight: 'bold'
  },
  intensityGroupSolid3: {
    background: '#FFFEA6',
    fontWeight: 'bold'
  },
  intensityGroupSolid4: {
    background: '#F7CDA0',
    fontWeight: 'bold'
  },
  intensityGroupSolid5: {
    background: '#EC5D57',
    fontWeight: 'bold',
    color: 'white'
  }
})

const DailyViewTable = (props: Props) => {
  const classes = useStyles()

  const DECIMAL_PLACES = 1

  const formatStationIntensityGroupByValue = (intensityGroup: number | undefined) => {
    switch (intensityGroup) {
      case 1:
        return classes.intensityGroupOutline1
      case 2:
        return classes.intensityGroupOutline2
      case 3:
        return classes.intensityGroupOutline3
      case 4:
        return classes.intensityGroupOutline4
      case 5:
        return classes.intensityGroupOutline5
      default:
        return
    }
  }

  const formatAreaMeanIntensityGroupByValue = (
    meanIntensityGroup: number | undefined
  ) => {
    switch (meanIntensityGroup) {
      case 1:
        return classes.intensityGroupSolid1
      case 2:
        return classes.intensityGroupSolid2
      case 3:
        return classes.intensityGroupSolid3
      case 4:
        return classes.intensityGroupSolid4
      case 5:
        return classes.intensityGroupSolid5
      default:
        return
    }
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
                <TableCell>HFI</TableCell>
                <TableCell>
                  M /
                  <br />
                  FIG
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
                        const stationCodesInPlanningArea: number[] = []
                        Object.entries(area.stations).forEach(([, station]) => {
                          stationCodesInPlanningArea.push(station.code)
                        })
                        const stationIntensityGroups: number[] = []
                        for (const code of stationCodesInPlanningArea) {
                          const stationDaily = props.dailiesMap.get(code)
                          if (stationDaily?.intensity_group !== undefined) {
                            stationIntensityGroups.push(stationDaily?.intensity_group)
                          }
                        }
                        const meanIntensityGroup = Math.round(
                          stationIntensityGroups.reduce((a, b) => a + b, 0) /
                            stationIntensityGroups.length
                        )
                        return (
                          <React.Fragment key={`zone-${areaName}`}>
                            <TableRow
                              className={classes.planningArea}
                              key={`zone-${areaName}`}
                            >
                              <TableCell className={classes.planningArea} colSpan={19}>
                                {area.name}
                              </TableCell>
                              <TableCell
                                className={formatAreaMeanIntensityGroupByValue(
                                  meanIntensityGroup
                                )}
                              >
                                {meanIntensityGroup}
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
                                    <TableCell>
                                      {daily?.hfi?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell
                                      className={formatStationIntensityGroupByValue(
                                        daily?.intensity_group
                                      )}
                                    >
                                      {daily?.intensity_group}
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
