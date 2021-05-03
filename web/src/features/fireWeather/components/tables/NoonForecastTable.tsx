import React from 'react'

import { NoonForecastValue } from 'api/forecastAPI'
import { formatDateInPST } from 'utils/date'
import { Column } from 'features/fireWeather/components/tables/SortableTableByDatetime'
import {
  comparisonTableStyles,
  formatPrecipitation,
  formatRelativeHumidity,
  formatTemperature,
  formatWindSpeedDirection
} from 'features/fireWeather/components/tables/StationComparisonTable'
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
import { ObservedValue } from 'api/observationAPI'

interface NoonForecastTableProps {
  noonForecasts: NoonForecastValue[] | undefined
  noonObservations: ObservedValue[] | undefined
}

const NoonForecastTable = (props: NoonForecastTableProps) => {
  const classes = comparisonTableStyles()

  return (
    <Paper className={classes.paper}>
      <Typography component="div" variant="subtitle2">
        Forecast and Observed noon weather
      </Typography>
      <Paper>
        <TableContainer>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell></TableCell>
                <TableCell className={classes.darkColumnHeader} colSpan={5}>
                  Temperature
                </TableCell>
                <TableCell className={classes.lightColumnHeader} colSpan={5}>
                  Relative Humidity
                </TableCell>
                <TableCell className={classes.darkColumnHeader} colSpan={5}>
                  Wind Speed + Direction
                </TableCell>
                <TableCell className={classes.lightColumnHeader} colSpan={5}>
                  Precipitation
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Date</TableCell>
                {/* Temperature */}
                <TableCell className={classes.darkColumnHeader}>Forecast</TableCell>
                <TableCell className={classes.darkColumnHeader}>Observed</TableCell>
                {/* Relative Humidity */}
                <TableCell className={classes.lightColumnHeader}>Forecast</TableCell>
                <TableCell className={classes.lightColumnHeader}>Observed</TableCell>
                {/* Wind Speed + Direction */}
                <TableCell className={classes.darkColumnHeader}>Forecast</TableCell>
                <TableCell className={classes.darkColumnHeader}>Observed</TableCell>
                {/* Precip */}
                <TableCell className={classes.lightColumnHeader}>Forecast</TableCell>
                <TableCell className={classes.lightColumnHeader}>Observed</TableCell>
              </TableRow>
            </TableHead>
            <TableBody></TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Paper>
  )
}

export default React.memo(NoonForecastTable)
