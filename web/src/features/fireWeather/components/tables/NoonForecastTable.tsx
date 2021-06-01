import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { NoonForecastValue } from 'api/forecastAPI'
import { formatDateInPST, formatDateInUTC00Suffix } from 'utils/date'
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
import ComparisonTableRow, { DataSource, WeatherVariable } from './ComparisonTableRow'

interface NoonForecastTableProps {
  testId?: string
  noonForecasts: NoonForecastValue[] | undefined
  noonObservations: ObservedValue[] | undefined
}

const useStyles = makeStyles({
  paper: {
    padding: '5px',
    // There's a formating issues that causes the last cell in the table to be cut off
    // when in 100%, on a small screen. Setting the width to 95% is a workaround, as the
    // true source of the problem remains a mystery. (suspicion: it's something to do with using
    // flex boxes, and having a table that needs to scroll.)
    width: '95%'
  },
  typography: {},
  lightColumnHeader: {
    textAlign: 'center',
    padding: '2px',
    minWidth: '60px'
  },
  lightColumn: {
    textAlign: 'right',
    padding: '2px'
  },
  windSpeedValue: {
    whiteSpace: 'nowrap'
  },
  relativeHumidityValue: {
    whiteSpace: 'nowrap'
  },
  windDirectionValue: {
    whiteSpace: 'nowrap'
  },
  precipitationValue: {
    whiteSpace: 'nowrap'
  },
  darkColumn: {
    backgroundColor: '#fafafa',
    padding: '2px',
    textAlign: 'right'
  },
  darkColumnHeader: {
    backgroundColor: 'rgb(240, 240, 240)',
    textAlign: 'center',
    padding: '2px',
    minWidth: '60px'
  }
})

const NoonForecastTable = (props: NoonForecastTableProps) => {
  const classes = useStyles()
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
  const headers: WeatherVariable[] = [
    'Temperature',
    'Relative Humidity',
    'Wind Speed + Direction',
    'Precipitation'
  ]
  const subheaders: DataSource[][] = [
    ['Forecast', 'Observed'],
    ['Forecast', 'Observed'],
    ['Forecast', 'Observed'],
    ['Forecast', 'Observed']
  ]

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
        <Paper className={classes.paper}>
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

                    const indexCell = (
                      <TableCell>{formatDateInPST(forecast.datetime)}</TableCell>
                    )

                    return (
                      <ComparisonTableRow
                        key={idx}
                        index={indexCell}
                        headers={headers}
                        subheaders={subheaders}
                        observation={observation}
                        forecast={forecast}
                        accumulatedObsPrecip={accumPrecip}
                        testId={`forecast-obs-comparison-table-row`}
                        testIdRowNumber={idx}
                      ></ComparisonTableRow>
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
