import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import Paper from '@material-ui/core/Paper'
import Typography from '@material-ui/core/Typography'

import { MODEL_VALUE_DECIMAL } from 'utils/constants'
import { ModelValue } from 'api/modelAPI'

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
  values: ModelValue[] | undefined
}

const DailyModelsDisplay = ({ values }: Props) => {
  const classes = useStyles()

  if (!values) {
    return null
  }

  return (
    <div className={classes.display} data-testid="daily-models-display">
      <Typography className={classes.title} variant="subtitle2" component="div">
        10 days of interpolated GDPS noon (12pm PST) values:
      </Typography>
      <Paper elevation={1}>
        <TableContainer>
          <Table className={classes.table} size="small" aria-label="weather data table">
            <TableBody>
              <TableRow>
                <TableCell>Date</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>{v.datetime.slice(0, 10)}</TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>Temp (°C)</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {v.temperature.toFixed(MODEL_VALUE_DECIMAL)}
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
                    {v.wind_speed.toFixed(MODEL_VALUE_DECIMAL)}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell>Precip (mm/cm)</TableCell>
                {values.map(v => (
                  <TableCell key={v.datetime}>
                    {v.total_precipitation.toFixed(MODEL_VALUE_DECIMAL)}
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

export default React.memo(DailyModelsDisplay)
