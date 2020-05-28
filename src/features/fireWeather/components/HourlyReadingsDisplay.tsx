import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import Paper from '@material-ui/core/Paper'
import Typography from '@material-ui/core/Typography'

import { HOURLY_VALUES_DECIMAL } from 'utils/constants'
import { ReadingValue } from 'api/readingAPI'
import { datetimeInPDT } from 'utils/date'

const useStyles = makeStyles({
  display: {
    paddingBottom: 16
  },
  table: {
    minWidth: 650
  },
  title: {
    paddingBottom: 4
  }
})

interface Props {
  values: ReadingValue[] | undefined
}

const HourlyReadingsDisplay = ({ values }: Props) => {
  const classes = useStyles()

  if (!values) {
    return null
  }

  return (
    <div className={classes.display} data-testid="hourly-readings-display">
      <Typography className={classes.title} component="div" variant="subtitle2">
        Past 5 days of hourly readings from station:
      </Typography>

      <Paper elevation={1}>
        <TableContainer>
          <Table className={classes.table} size="small" aria-label="weather data table">
            <TableBody>
              <TableRow>
                <TableCell>Date (PDT)</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>{datetimeInPDT(v.datetime)}</TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>Temp (°C)</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {v.temperature.toFixed(HOURLY_VALUES_DECIMAL)}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>RH (%)</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {Math.round(v.relative_humidity)}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>Wind Dir</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>{Math.round(v.wind_direction)}</TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>Wind Spd (km/h)</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {v.wind_speed.toFixed(HOURLY_VALUES_DECIMAL)}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>Precip (mm/cm)</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {v.precipitation.toFixed(HOURLY_VALUES_DECIMAL)}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>FFMC</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {v.ffmc?.toFixed(HOURLY_VALUES_DECIMAL)}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>ISI</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {v.isi?.toFixed(HOURLY_VALUES_DECIMAL)}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>FWI</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {v.fwi?.toFixed(HOURLY_VALUES_DECIMAL)}
                  </TableCell>
                ))}
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(HourlyReadingsDisplay)
