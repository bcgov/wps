import React, { useState } from 'react'

import { NoonForecastValue } from 'api/forecastAPI'
import { formatDateInPST, formatDateInUTC00Suffix } from 'utils/date'
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
import { getDatetimeComparator, Order, calculateAccumulatedPrecip } from 'utils/table'
import ExpandMoreIcon from '@material-ui/icons/ExpandMore'

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
            <Table stickyHeader size="small" data-testid={`${props.testId}`}>
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
                    const forecastDatetime = formatDateInUTC00Suffix(forecast.datetime)

                    const accumPrecip = calculateAccumulatedPrecip(
                      forecastDatetime,
                      observationsRowsSortedByDatetime
                    )

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
                            accumPrecip?.precipitation,
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
