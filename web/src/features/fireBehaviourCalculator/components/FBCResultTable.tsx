import React from 'react'

import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { FBCStation } from 'api/fbCalcAPI'

interface Props {
  testId?: string
  fireBehaviourResultStations: FBCStation[]
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
    maxWidth: 1900
  }
})

const FBCResultTable = (props: Props) => {
  const classes = useStyles()

  const DECIMAL_PLACES = 1

  return (
    <div className={classes.display} data-testid={props.testId}>
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
                <TableCell>HFI</TableCell>
                <TableCell>
                  ROS
                  <br />
                  (m/min)
                </TableCell>
                <TableCell>Fire Type</TableCell>
                <TableCell>CFB (%)</TableCell>
                <TableCell>
                  Flame <br />
                  Length <br /> (m)
                </TableCell>
                <TableCell>
                  30 min <br />
                  fire size <br />
                  (hectares)
                </TableCell>
                <TableCell>
                  60 min <br />
                  fire size <br />
                  (hectares)
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {props.fireBehaviourResultStations.map((stationResult, index) => {
                return (
                  <TableRow key={index}>
                    <TableCell>
                      {stationResult.station_code} - {stationResult.station_name}
                    </TableCell>
                    <TableCell>{stationResult.elevation}</TableCell>
                    <TableCell>{stationResult.fuel_type}</TableCell>
                    <TableCell>{stationResult.status}</TableCell>
                    <TableCell>{stationResult.temp}</TableCell>
                    <TableCell>{stationResult.rh}</TableCell>
                    <TableCell>{stationResult.wind_direction}</TableCell>
                    <TableCell>{stationResult.wind_speed}</TableCell>
                    <TableCell>{stationResult.precipitation}</TableCell>
                    <TableCell>{stationResult.grass_cure}</TableCell>
                    <TableCell>
                      {stationResult.fine_fuel_moisture_code.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.duff_moisture_code.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.drought_code.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.initial_spread_index.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.build_up_index.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.fire_weather_index.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.head_fire_intensity.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.rate_of_spread.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>{stationResult.fire_type}</TableCell>
                    <TableCell>
                      {/* CFB comes in as a number 0 to 1, so we multiple by 100 to get the percentage */}
                      {(stationResult.percentage_crown_fraction_burned * 100).toFixed(
                        DECIMAL_PLACES
                      )}
                    </TableCell>
                    <TableCell>
                      {stationResult.flame_length.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.thirty_minute_fire_size.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {stationResult.sixty_minute_fire_size.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(FBCResultTable)
