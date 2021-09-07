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
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import { isGrassFuelType } from 'features/hfiCalculator/validation'
import {
  calculateMeanIntensityGroup,
  intensityGroupColours
} from 'features/hfiCalculator/components/meanIntensity'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import { isUndefined } from 'lodash'

export interface Props {
  title: string
  fireCentres: Record<string, FireCentre>
  dailiesMap: Map<number, StationDaily>
  currentDay: string
  previousDay: () => void
  nextDay: () => void
  testId?: string
}

const prepLevelColours: { [description: string]: string } = {
  green: '#A0CD63',
  blue: '#4CAFEA',
  yellow: '#FFFD54',
  orange: '#F6C142',
  brightRed: '#EA3223',
  bloodRed: '#B02318'
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
    backgroundColor: 'rgba(40, 53, 147, 0.05)',

    '& .MuiTableCell-sizeSmall': {
      paddingLeft: '12px'
    }
  },
  fireStarts: {
    fontWeight: 'bold',
    textAlign: 'center'
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
    border: '2px solid',
    borderColor: intensityGroupColours.lightGreen,
    borderRadius: '4px',
    textAlign: 'center'
  },
  intensityGroupOutline2: {
    border: '2px solid',
    borderColor: intensityGroupColours.cyan,
    borderRadius: '4px',
    textAlign: 'center'
  },
  intensityGroupOutline3: {
    border: '2px solid',
    borderColor: intensityGroupColours.yellow,
    borderRadius: '4px',
    textAlign: 'center'
  },
  intensityGroupOutline4: {
    border: '2px solid',
    borderColor: intensityGroupColours.orange,
    borderRadius: '4px',
    textAlign: 'center'
  },
  intensityGroupOutline5: {
    border: '2px solid',
    borderColor: intensityGroupColours.red,
    borderRadius: '4px',
    textAlign: 'center'
  },
  intensityGroupSolid1: {
    background: intensityGroupColours.lightGreen,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  intensityGroupSolid2: {
    background: intensityGroupColours.cyan,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  intensityGroupSolid3: {
    background: intensityGroupColours.yellow,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  intensityGroupSolid4: {
    background: intensityGroupColours.orange,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  intensityGroupSolid5: {
    background: intensityGroupColours.red,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center'
  },
  prepLevel1: {
    background: prepLevelColours.green,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel2: {
    background: prepLevelColours.blue,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel3: {
    background: prepLevelColours.yellow,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel4: {
    background: prepLevelColours.orange,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel5: {
    background: prepLevelColours.brightRed,
    fontWeight: 'bold',
    textAlign: 'center',
    color: 'white'
  },
  prepLevel6: {
    background: prepLevelColours.bloodRed,
    fontWeight: 'bold',
    textAlign: 'center',
    color: 'white'
  }
})

export const DailyViewTable = (props: Props): JSX.Element => {
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

  const formatPrepLevelByValue = (prepLevel: number | undefined) => {
    switch (prepLevel) {
      case 1:
        return classes.prepLevel1
      case 2:
        return classes.prepLevel2
      case 3:
        return classes.prepLevel3
      case 4:
        return classes.prepLevel4
      case 5:
        return classes.prepLevel5
      case 6:
        return classes.prepLevel6
      default:
        return
    }
  }

  const calculatePrepLevel = (meanIntensityGroup: number | undefined) => {
    // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
    if (isUndefined(meanIntensityGroup)) {
      return undefined
    }
    if (meanIntensityGroup < 3) {
      return 1
    }
    if (meanIntensityGroup < 4) {
      return 2
    }
    if (meanIntensityGroup < 5) {
      return 3
    }
    return 4
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
                  60 min <br />
                  fire size <br />
                  (hectares)
                </TableCell>
                <TableCell>
                  Fire
                  <br />
                  Type
                </TableCell>
                <TableCell>
                  M /
                  <br />
                  FIG
                </TableCell>
                <TableCell>
                  Fire
                  <br />
                  Starts
                </TableCell>
                <TableCell>
                  Prep
                  <br />
                  Level
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
                        const meanIntensityGroup = calculateMeanIntensityGroup(
                          area,
                          props.dailiesMap
                        )
                        const prepLevel = calculatePrepLevel(meanIntensityGroup)
                        return (
                          <React.Fragment key={`zone-${areaName}`}>
                            <TableRow
                              className={classes.planningArea}
                              key={`zone-${areaName}`}
                              data-testid={`zone-${areaName}`}
                            >
                              <TableCell className={classes.planningArea} colSpan={21}>
                                {area.name}
                              </TableCell>
                              {/* <TableCell
                                className={formatAreaMeanIntensityGroupByValue(
                                  meanIntensityGroup
                                )}
                                data-testid={`zone-${areaName}-mean-intensity`}
                              >
                                {meanIntensityGroup}
                              </TableCell> */}
                              <MeanIntensityGroupRollup
                                area={area}
                                dailiesMap={props.dailiesMap}
                              ></MeanIntensityGroupRollup>
                              <TableCell
                                className={classes.fireStarts}
                                data-testid={`daily-fire-starts-${areaName}`}
                              >
                                {/* using a fixed value of 0-1 Fire Starts for now */}
                                0-1
                              </TableCell>
                              <TableCell
                                className={formatPrepLevelByValue(prepLevel)}
                                data-testid={`daily-prep-level-${areaName}`}
                              >
                                {prepLevel}
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
                                    <GrassCureCell
                                      value={daily?.grass_cure_percentage}
                                      isGrassFuelType={isGrassFuelType(
                                        station.station_props
                                      )}
                                    ></GrassCureCell>
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
                                    <TableCell data-testid={`${daily?.code}-ros`}>
                                      {daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell data-testid={`${daily?.code}-hfi`}>
                                      {daily?.hfi?.toFixed(DECIMAL_PLACES)}
                                    </TableCell>
                                    <TableCell data-testid={`${daily?.code}-1-hr-size`}>
                                      {daily?.sixty_minute_fire_size?.toFixed(
                                        DECIMAL_PLACES
                                      )}
                                    </TableCell>
                                    <TableCell data-testid={`${daily?.code}-fire-type`}>
                                      {daily?.fire_type}
                                    </TableCell>
                                    <TableCell
                                      className={formatStationIntensityGroupByValue(
                                        daily?.intensity_group
                                      )}
                                      data-testid={`${daily?.code}-intensity-group`}
                                    >
                                      {daily?.intensity_group}
                                    </TableCell>
                                    <TableCell colSpan={2}>
                                      {/* empty cell for spacing (Fire Starts & Prev Level columns) */}
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
