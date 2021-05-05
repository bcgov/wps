import React, { useState } from 'react'

import { NoonForecastValue } from 'api/forecastAPI'
import { formatDateInPST } from 'utils/date'
import {
  comparisonTableStyles,
  formatPrecipitation,
  formatRelativeHumidity,
  formatTemperature,
  formatWindSpeedDirection
} from 'features/fireWeather/components/tables/StationComparisonTable'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Typography
} from '@material-ui/core'
import { ObservedValue } from 'api/observationAPI'
import { getDatetimeComparator, Order } from 'utils/table'
import ExpandMoreIcon from '@material-ui/icons/ExpandMore'
import { DateTime } from 'luxon'

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

  if (props.noonForecasts.length === 0 && props.noonObservations.length === 0) {
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

  const calculateAccumulatedPrecip = (
    today: ObservedValue | undefined,
    yesterday: ObservedValue | undefined
  ): number | undefined => {
    if (!today || !yesterday) {
      return undefined
    }
    if (!today.precipitation || !yesterday.precipitation) {
      return undefined
    }
    return today.precipitation - yesterday.precipitation
  }

  return (
    <Accordion defaultExpanded>
      <AccordionSummary
        data-testid={`${props.testId}-accordion`}
        expandIcon={<ExpandMoreIcon />}
      >
        <Typography component="div" variant="subtitle2">
          Forecast and Observed noon weather:
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
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
                  <TableCell sortDirection={order}>
                    <TableSortLabel direction={order} onClick={toggleDatetimeOrder}>
                      Date (PST)
                    </TableSortLabel>
                  </TableCell>
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
                {forecastRowsSortedByDatetime.map(
                  (forecast: NoonForecastValue, idx: number) => {
                    const observation = observationsRowsSortedByDatetime.find(
                      obs => obs.datetime === forecast.datetime
                    )
                    const forecastDatetime = DateTime.fromISO(
                      forecast.datetime
                    ).toJSDate()
                    const yesterdaysDatetime = forecastDatetime
                    yesterdaysDatetime.setHours(forecastDatetime.getHours() - 24)
                    const yesterdaysObservation = observationsRowsSortedByDatetime.find(
                      obs =>
                        DateTime.fromISO(obs.datetime).toJSDate() === yesterdaysDatetime
                    )

                    console.log(forecastDatetime)
                    console.log(yesterdaysDatetime)
                    console.log(observation)
                    console.log(yesterdaysObservation)

                    return (
                      <TableRow key={idx}>
                        <TableCell>{formatDateInPST(forecast.datetime)}</TableCell>
                        {/* Temperature */}
                        <TableCell className={classes.darkColumn}>
                          {formatTemperature(forecast)}
                        </TableCell>
                        <TableCell className={classes.darkColumn}>
                          {formatTemperature(observation)}
                        </TableCell>
                        {/* Relative Humidity */}
                        <TableCell className={classes.lightColumn}>
                          {formatRelativeHumidity(
                            forecast,
                            classes.relativeHumidityValue
                          )}
                        </TableCell>
                        <TableCell className={classes.lightColumn}>
                          {formatRelativeHumidity(
                            observation,
                            classes.relativeHumidityValue
                          )}
                        </TableCell>
                        {/* Wind Speed + Direction */}
                        <TableCell className={classes.darkColumn}>
                          {formatWindSpeedDirection(
                            forecast,
                            classes.windSpeedValue,
                            classes.windDirectionValue
                          )}
                        </TableCell>
                        <TableCell className={classes.darkColumn}>
                          {formatWindSpeedDirection(
                            observation,
                            classes.windSpeedValue,
                            classes.windDirectionValue
                          )}
                        </TableCell>
                        {/* Precipitation  */}
                        <TableCell className={classes.lightColumn}>
                          {formatPrecipitation(
                            forecast.total_precipitation,
                            classes.precipitationValue
                          )}
                        </TableCell>
                        <TableCell className={classes.lightColumn}>
                          {formatPrecipitation(
                            calculateAccumulatedPrecip(
                              observation,
                              yesterdaysObservation
                            ),
                            classes.precipitationValue
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  }
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </AccordionDetails>
    </Accordion>
  )
}

export default React.memo(NoonForecastTable)
