import React from 'react'
import { useSelector } from 'react-redux'
import { makeStyles } from '@material-ui/core/styles'

import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import Paper from '@material-ui/core/Paper'
import Typography from '@material-ui/core/Typography'
import moment from 'moment'

import { selectHourlies } from 'app/rootReducer'
import { ErrorMessage } from 'components/ErrorMessage'
import { HOURLY_VALUES_DECIMAL, PDT_UTC_OFFSET } from 'utils/constants'

const useStyles = makeStyles({
  table: {
    minWidth: 650
  },
  station: {
    paddingTop: 8,
    paddingLeft: 16
  },
  hourlies: {
    marginBottom: 20
  }
})

export const HourlyReadingsDisplay = () => {
  const classes = useStyles()
  const { error, hourlies } = useSelector(selectHourlies)

  if (error) {
    return (
      <ErrorMessage
        error={error}
        context="while fetching hourly readings"
        marginTop={5}
      />
    )
  }

  if (hourlies.length === 0) {
    return null
  }

  return (
    <div data-testid="hourly-readings-displays">
      {hourlies.map(({ station, values }) => (
        <Paper className={classes.hourlies} key={station.code}>
          <Typography className={classes.station} variant="subtitle1" component="div">
            Hourly readings for weather station: {`${station.name} (${station.code})`}
          </Typography>
          <TableContainer>
            <Table className={classes.table} size="small" aria-label="weather data table">
              <TableBody>
                <TableRow>
                  <TableCell align="left">Date (PDT)</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {moment(v.datetime)
                        .utcOffset(PDT_UTC_OFFSET)
                        .format('YYYY-MM-DD HH:mm')}
                    </TableCell>
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell>Temperature</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {v.temperature.toFixed(HOURLY_VALUES_DECIMAL)}
                    </TableCell>
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell>Relative Humidity</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {Math.round(v.relative_humidity)}
                    </TableCell>
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell>Wind Speed</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {v.wind_speed.toFixed(HOURLY_VALUES_DECIMAL)}
                    </TableCell>
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell>Wind Direction</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {Math.round(v.wind_direction)}
                    </TableCell>
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell>Precipitation</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {v.precipitation.toFixed(HOURLY_VALUES_DECIMAL)}
                    </TableCell>
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell>FFMC</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {v.ffmc?.toFixed(HOURLY_VALUES_DECIMAL)}
                    </TableCell>
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell>ISI</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {v.isi?.toFixed(HOURLY_VALUES_DECIMAL)}
                    </TableCell>
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell>FWI</TableCell>
                  {values.map(v => (
                    <TableCell key={v.datetime} align="left">
                      {v.fwi?.toFixed(HOURLY_VALUES_DECIMAL)}
                    </TableCell>
                  ))}
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      ))}
    </div>
  )
}
