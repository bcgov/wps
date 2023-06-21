import React, { useState } from 'react'
import { styled } from '@mui/material/styles'

import { NoonForecastValue } from 'api/forecastAPI'
import { formatDatetimeInPST, formatDateInUTC00Suffix } from 'utils/date'
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
} from '@mui/material'
import { ObservedValue } from 'api/observationAPI'
import { getDatetimeComparator, Order, calculateAccumulatedPrecip } from 'utils/table'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ComparisonTableRow, { DataSource, WeatherVariable } from './ComparisonTableRow'

const PREFIX = 'NoonForecastTable'

const classes = {
  paper: `${PREFIX}-paper`,
  typography: `${PREFIX}-typography`,
  lightColumnHeader: `${PREFIX}-lightColumnHeader`,
  lightColumn: `${PREFIX}-lightColumn`,
  windSpeedValue: `${PREFIX}-windSpeedValue`,
  relativeHumidityValue: `${PREFIX}-relativeHumidityValue`,
  windDirectionValue: `${PREFIX}-windDirectionValue`,
  precipitationValue: `${PREFIX}-precipitationValue`,
  darkColumn: `${PREFIX}-darkColumn`,
  darkColumnHeader: `${PREFIX}-darkColumnHeader`
}

const StyledAccordion = styled(Accordion)({
  [`& .${classes.paper}`]: {
    padding: '5px',
    // There's a formating issues that causes the last cell in the table to be cut off
    // when in 100%, on a small screen. Setting the width to 95% is a workaround, as the
    // true source of the problem remains a mystery. (suspicion: it's something to do with using
    // flex boxes, and having a table that needs to scroll.)
    width: '95%'
  },
  [`& .${classes.typography}`]: {},
  [`& .${classes.lightColumnHeader}`]: {
    textAlign: 'center',
    padding: '2px',
    minWidth: '60px'
  },
  [`& .${classes.lightColumn}`]: {
    textAlign: 'right',
    padding: '2px'
  },
  [`& .${classes.windSpeedValue}`]: {
    whiteSpace: 'nowrap'
  },
  [`& .${classes.relativeHumidityValue}`]: {
    whiteSpace: 'nowrap'
  },
  [`& .${classes.windDirectionValue}`]: {
    whiteSpace: 'nowrap'
  },
  [`& .${classes.precipitationValue}`]: {
    whiteSpace: 'nowrap'
  },
  [`& .${classes.darkColumn}`]: {
    backgroundColor: '#fafafa',
    padding: '2px',
    textAlign: 'right'
  },
  [`& .${classes.darkColumnHeader}`]: {
    backgroundColor: 'rgb(240, 240, 240)',
    textAlign: 'center',
    padding: '2px',
    minWidth: '60px'
  }
})

interface NoonForecastTableProps {
  testId?: string
  noonForecasts: NoonForecastValue[] | undefined
  noonObservations: ObservedValue[] | undefined
}

const NoonForecastTable = (props: NoonForecastTableProps) => {
  const [order, setOrder] = useState<Order>('desc')

  if (props.noonForecasts === undefined || props.noonObservations === undefined) {
    return null
  }

  if (props.noonForecasts.length === 0 && props.noonObservations.length === 0) {
    return null
  }

  const forecastRowsSortedByDatetime = [...props.noonForecasts].sort(getDatetimeComparator(order))
  const observationsRowsSortedByDatetime = [...props.noonObservations].sort(getDatetimeComparator(order))
  const toggleDatetimeOrder = () => {
    setOrder(order === 'asc' ? 'desc' : 'asc')
  }
  const headers: WeatherVariable[] = [
    'Temperature',
    'Relative Humidity',
    'Wind Speed',
    'Wind Direction',
    'Precipitation'
  ]
  const subheaders: DataSource[][] = [
    ['Forecast', 'Observed'],
    ['Forecast', 'Observed'],
    ['Forecast', 'Observed'],
    ['Forecast', 'Observed'],
    ['Forecast', 'Observed']
  ]

  return (
    <StyledAccordion defaultExpanded>
      <AccordionSummary data-testid={`${props.testId}-accordion`} expandIcon={<ExpandMoreIcon />}>
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
                    Temperature (&deg;C)
                  </TableCell>
                  <TableCell className={classes.lightColumnHeader} colSpan={2}>
                    Relative Humidity (%)
                  </TableCell>
                  <TableCell className={classes.darkColumnHeader} colSpan={2}>
                    Wind Speed (km/h)
                  </TableCell>
                  <TableCell className={classes.darkColumnHeader} colSpan={2}>
                    Wind Direction (&deg;)
                  </TableCell>
                  <TableCell className={classes.lightColumnHeader} colSpan={2}>
                    Precipitation (mm)
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sortDirection={order}>
                    <TableSortLabel direction={order} onClick={toggleDatetimeOrder}>
                      Date (PST)
                    </TableSortLabel>
                  </TableCell>
                  {/* Temperature */}
                  <TableCell className={classes.darkColumnHeader}>FCST</TableCell>
                  <TableCell className={classes.darkColumnHeader}>OBS</TableCell>
                  {/* Relative Humidity */}
                  <TableCell className={classes.lightColumnHeader}>FCST</TableCell>
                  <TableCell className={classes.lightColumnHeader}>OBS</TableCell>
                  {/* Wind Speed */}
                  <TableCell className={classes.darkColumnHeader}>FCST</TableCell>
                  <TableCell className={classes.darkColumnHeader}>OBS</TableCell>
                  {/* Wind Direction */}
                  <TableCell className={classes.darkColumnHeader}>FCST</TableCell>
                  <TableCell className={classes.darkColumnHeader}>OBS</TableCell>
                  {/* Precip */}
                  <TableCell className={classes.lightColumnHeader}>FCST</TableCell>
                  <TableCell className={classes.lightColumnHeader}>OBS</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {forecastRowsSortedByDatetime.map((forecast: NoonForecastValue, idx: number) => {
                  const observation = observationsRowsSortedByDatetime.find(obs => obs.datetime === forecast.datetime)
                  const forecastDatetime = formatDateInUTC00Suffix(forecast.datetime)

                  const accumPrecip = calculateAccumulatedPrecip(forecastDatetime, observationsRowsSortedByDatetime)

                  const indexCell = <TableCell>{formatDatetimeInPST(forecast.datetime)}</TableCell>

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
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </AccordionDetails>
    </StyledAccordion>
  )
}

export default React.memo(NoonForecastTable)
