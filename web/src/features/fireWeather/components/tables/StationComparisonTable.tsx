import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { ClassNameMap } from '@material-ui/styles/withStyles'
import Paper from '@material-ui/core/Paper'
import Typography from '@material-ui/core/Typography'
import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import TableHead from '@material-ui/core/TableHead'
import { GeoJsonStation } from 'api/stationAPI'
import { ObservedValue } from 'api/observationAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ModelValue } from 'api/modelAPI'
import { formatDateInUTC00Suffix, formatDateInPST } from 'utils/date'
import { calculateAccumulatedPrecip } from 'utils/table'
import ComparisonTableRow, { DataSource, WeatherVariable } from './ComparisonTableRow'

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
interface Props {
  timeOfInterest: string
  stationCodes: number[]
  stationsByCode: Record<number, GeoJsonStation | undefined>
  allNoonForecastsByStation: Record<number, NoonForecastValue[] | undefined>
  observationsByStation: Record<number, ObservedValue[] | undefined>
  allHighResModelsByStation: Record<number, ModelValue[] | undefined>
  allRegionalModelsByStation: Record<number, ModelValue[] | undefined>
  allModelsByStation: Record<number, ModelValue[] | undefined>
}

const findNoonMatch = (
  noonDate: string,
  collection: ModelValue[] | undefined
): ModelValue | undefined => {
  return collection?.find((item: ModelValue) => item.datetime === noonDate)
}

const SubHeadings = (
  value: string,
  index: number,
  classes: ClassNameMap<'darkColumnHeader' | 'lightColumnHeader'>
) => {
  const className = index % 2 === 0 ? classes.darkColumnHeader : classes.lightColumnHeader
  return [
    <TableCell key={`${value}-observered-${index}`} className={className}>
      Observed
    </TableCell>,
    <TableCell key={`${value}-forecast-${index}`} className={className}>
      Forecast
    </TableCell>,
    <TableCell key={`${value}-HRDPS-${index}`} className={className}>
      HRDPS
    </TableCell>,
    <TableCell key={`${value}-RDPS-${index}`} className={className}>
      RDPS
    </TableCell>,
    <TableCell key={`${value}-GDPS-${index}`} className={className}>
      GDPS
    </TableCell>
  ]
}

const StationComparisonTable = (props: Props) => {
  const classes = useStyles()
  // format the date to match the ISO format in the API for easy comparison.
  const noonDate = formatDateInUTC00Suffix(props.timeOfInterest)
  return (
    <Paper className={classes.paper}>
      <Typography component="div" variant="subtitle2">
        Station comparison for {formatDateInPST(noonDate)} PDT
      </Typography>
      <Paper>
        <TableContainer>
          <Table
            size="small"
            aria-label="sortable wx table"
            data-testid="station-comparison-table"
          >
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
                <TableCell className={classes.darkColumnHeader}>Dew point</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Weather Stations</TableCell>
                {['temp', 'rh', 'wind', 'precip'].map((value, index) => {
                  return SubHeadings(value, index, classes)
                })}
                {/* Dew Point */}
                <TableCell className={classes.darkColumnHeader}>Observed</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {props.stationCodes.map((stationCode: number, idx: number) => {
                const station = props.stationsByCode[stationCode]
                const noonForecasts = props.allNoonForecastsByStation[stationCode]
                const noonForecast = noonForecasts?.find(
                  forecast => forecast.datetime === noonDate
                )
                const observations = props.observationsByStation[stationCode]
                const observation = observations?.find(item => item.datetime === noonDate)
                const accumulatedObservedPrecipitation = calculateAccumulatedPrecip(
                  noonDate,
                  observations
                )
                const hrdpsModelPrediction = findNoonMatch(
                  noonDate,
                  props.allHighResModelsByStation[stationCode]
                )
                const accumulatedHRDPSPrecipitation = calculateAccumulatedPrecip(
                  noonDate,
                  props.allHighResModelsByStation[stationCode]
                )
                const rdpsModelPrediction = findNoonMatch(
                  noonDate,
                  props.allRegionalModelsByStation[stationCode]
                )
                const accumulatedRDPSPrecipitation = calculateAccumulatedPrecip(
                  noonDate,
                  props.allRegionalModelsByStation[stationCode]
                )
                const gdpsModelPrediction = findNoonMatch(
                  noonDate,
                  props.allModelsByStation[stationCode]
                )
                const accumulatedGDPSPrecipitation = calculateAccumulatedPrecip(
                  noonDate,
                  props.allModelsByStation[stationCode]
                )
                const indexCell = (
                  <TableCell>
                    {station?.properties.name} ({stationCode})
                  </TableCell>
                )

                const headers = [
                    WeatherVariable.Temperature,
                    WeatherVariable['Relative Humidity'],
                    WeatherVariable['Wind Speed + Direction'],
                    WeatherVariable.Precipitation,
                    WeatherVariable['Dew point']
                  ]
                const subheaders = [
                    [
                      DataSource.Observed,
                      DataSource.Forecast,
                      DataSource.HRDPS,
                      DataSource.RDPS,
                      DataSource.GDPS
                    ],
                    [
                      DataSource.Observed,
                      DataSource.Forecast,
                      DataSource.HRDPS,
                      DataSource.RDPS,
                      DataSource.GDPS
                    ],
                    [
                      DataSource.Observed,
                      DataSource.Forecast,
                      DataSource.HRDPS,
                      DataSource.RDPS,
                      DataSource.GDPS
                    ],
                    [
                      DataSource.Observed,
                      DataSource.Forecast,
                      DataSource.HRDPS,
                      DataSource.RDPS,
                      DataSource.GDPS
                    ],
                    [DataSource.Observed]
                  ]

                return (
                  <ComparisonTableRow
                    index={indexCell}
                    headers={headers}
                    subheaders={subheaders}
                    observation={observation}
                    forecast={noonForecast}
                    highResModel={hrdpsModelPrediction}
                    regionalModel={rdpsModelPrediction}
                    globalModel={gdpsModelPrediction}
                    accumulatedHRDPSPrecip={accumulatedHRDPSPrecipitation}
                    accumulatedRDPSPrecip={accumulatedRDPSPrecipitation}
                    accumulatedGDPSPrecip={accumulatedGDPSPrecipitation}
                    accumulatedObsPrecip={accumulatedObservedPrecipitation}
                    testId={`comparison-table-row-${idx}`}
                    key={idx}
                  />
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Paper>
  )
}

export default React.memo(StationComparisonTable)
