import React, { useState } from 'react'

import { Forecast, NoonForecastValue } from 'api/forecastAPI'
import { formatDateInPST } from 'utils/date'
import {
  Column,
  WeatherValue
} from 'features/fireWeather/components/tables/SortableTableByDatetime'
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
import { getDatetimeComparator, Order } from 'utils/table'

interface NoonForecastTableProps {
  testId?: string
  noonForecasts: NoonForecastValue[] | undefined
  noonObservations: ObservedValue[] | undefined
}

const NoonForecastTable = (props: NoonForecastTableProps) => {
  const classes = comparisonTableStyles()
  const [order, setOrder] = useState<Order>('desc')

  if (props.noonForecasts === undefined || props.noonObservations === undefined) {
    return null
  }

  if ( props.noonForecasts.length === 0 && props.noonObservations.length === 0 ) {
    return null
  }

  const forecastRowsSortedByDatetime = [...props.noonForecasts].sort(
    getDatetimeComparator(order)
  )
  const observationsRowsSortedByDatetime = [...props.noonObservations].sort(
    getDatetimeComparator(order)
  )
  const toggleDatetimeOrder = () => {
    setOrder(order === 'asc' ? 'desc' : 'asc')
  }

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
                <TableCell className={classes.darkColumnHeader} colSpan={2}>
                  Temperature
                </TableCell>
                <TableCell className={classes.lightColumnHeader} colSpan={2}>
                  Relative Humidity
                </TableCell>
                <TableCell className={classes.darkColumnHeader} colSpan={2}>
                  Wind Speed + Direction
                </TableCell>
                <TableCell className={classes.lightColumnHeader} colSpan={2}>
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
            <TableBody>
              {forecastRowsSortedByDatetime.map((forecast: NoonForecastValue, idx: number) => {
                const observation = observationsRowsSortedByDatetime.find(obs => obs.datetime === forecast.datetime)
                return (
                  <TableRow key={idx}>
                    <TableCell>
                      {forecast.datetime}
                    </TableCell>
                    {/* Temperature */}
                    <TableCell>{formatTemperature(forecast)}</TableCell>
                    <TableCell>{formatTemperature(observation)}</TableCell>
                    {/* Relative Humidity */}
                    <TableCell>{formatRelativeHumidity(forecast, classes.relativeHumidityValue)}</TableCell>
                    <TableCell>{formatRelativeHumidity(observation, classes.relativeHumidityValue)}</TableCell>
                    {/* Wind Speed + Direction */}
                    <TableCell>{formatWindSpeedDirection(forecast, classes.windSpeedValue, classes.windDirectionValue)}</TableCell>
                    <TableCell>{formatWindSpeedDirection(observation, classes.windSpeedValue, classes.windDirectionValue)}</TableCell>
                    {/* Precipitation  */}
                    <TableCell>{formatPrecipitation(0.0, classes.precipitationValue)}</TableCell>
                    <TableCell>{formatPrecipitation(0.1, classes.precipitationValue)}</TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Paper>
  )
}

export default React.memo(NoonForecastTable)
