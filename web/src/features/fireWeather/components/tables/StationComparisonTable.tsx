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
import ToolTip from '@material-ui/core/Tooltip'
import { GeoJsonStation } from 'api/stationAPI'
import { ObservedValue } from 'api/observationAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ModelValue } from 'api/modelAPI'
import { formatDateInUTC00Suffix, formatDateInPST } from 'utils/date'
import { calculateAccumulatedPrecip, AccumulatedPrecipitation } from 'utils/table'
import {
  TEMPERATURE_VALUES_DECIMAL,
  RH_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL,
  PRECIP_VALUES_DECIMAL,
  DEW_POINT_VALUES_DECIMAL
} from 'utils/constants'

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

type TemperatureSourceType = NoonForecastValue | ObservedValue | ModelValue | undefined

const formatTemperature = (source: TemperatureSourceType) => {
  return (
    <div>
      {typeof source?.temperature === 'number' &&
        `${source?.temperature?.toFixed(TEMPERATURE_VALUES_DECIMAL)}${String.fromCharCode(
          176
        )}C`}
    </div>
  )
}

const formatModelTemperature = (source: ModelValue | undefined) => {
  const tooltip = (source as ModelValue)?.model_run_datetime
  return (
    source && (
      <ToolTip title={`model run time: ${tooltip}`} aria-label="temperature" arrow>
        {formatTemperature(source)}
      </ToolTip>
    )
  )
}

const formatRelativeHumidity = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  valueClassName: string
) => {
  return (
    <div className={valueClassName}>
      {typeof source?.relative_humidity === 'number' &&
        `${source?.relative_humidity?.toFixed(RH_VALUES_DECIMAL)}%`}
    </div>
  )
}

const formatModelRelativeHumidity = (
  source: ModelValue | undefined,
  valueClassName: string
) => {
  const tooltip = (source as ModelValue)?.model_run_datetime
  return (
    <ToolTip title={`model run time: ${tooltip}`} aria-label="Relative humidity" arrow>
      {formatRelativeHumidity(source, valueClassName)}
    </ToolTip>
  )
}

const formatWindSpeedDirection = (
  source:
    | Pick<NoonForecastValue | ObservedValue, 'wind_speed' | 'wind_direction'>
    | undefined,
  windSpeedClassName: string,
  windDirectionClassName: string
) => {
  return (
    <div>
      {typeof source?.wind_speed === 'number' && (
        <div className={windSpeedClassName}>
          {source?.wind_speed?.toFixed(WIND_SPEED_VALUES_DECIMAL)} km/h
        </div>
      )}
      {typeof source?.wind_speed === 'number' &&
        typeof source?.wind_direction === 'number' &&
        ' '}
      {typeof source?.wind_direction === 'number' && (
        <div className={windDirectionClassName}>
          {source?.wind_direction?.toFixed(WIND_SPEED_VALUES_DECIMAL)}
          {source?.wind_direction && String.fromCharCode(176)}
        </div>
      )}
    </div>
  )
}

const formatModelWindSpeedDirection = (
  source: ModelValue | undefined,
  windSpeedClassName: string,
  windDirectionClassName: string
) => {
  const tooltip = (source as ModelValue)?.model_run_datetime
  return (
    source && (
      <ToolTip
        title={`model run time: ${tooltip}`}
        aria-label="Wind speed and direction"
        arrow
      >
        {formatWindSpeedDirection(
          {
            wind_speed: source.wind.wind_speed ? source.wind.wind_speed : null,
            wind_direction: source.wind_direction ? source.wind_direction : null
          },
          windSpeedClassName,
          windDirectionClassName
        )}
      </ToolTip>
    )
  )
}

const formatPrecipitation = (
  precipitation: number | null | undefined,
  precipitationClassName: string
) => {
  return (
    <div className={precipitationClassName}>
      {typeof precipitation === 'number' &&
        `${precipitation.toFixed(PRECIP_VALUES_DECIMAL)} mm`}
    </div>
  )
}

const formatAccumulatedPrecipitation = (
  precipitation: AccumulatedPrecipitation | undefined,
  precipitationClassName: string
) => {
  const title: JSX.Element[] = []
  precipitation?.values.forEach((value, index) => {
    if ('delta_precipitation' in value && 'model_run_datetime' in value) {
      title.push(
        <div key={index}>
          prediction: {value.datetime}, precipitation:{' '}
          {value.delta_precipitation?.toFixed(PRECIP_VALUES_DECIMAL)} mm (model:{' '}
          {value.model_run_datetime})
        </div>
      )
    } else if ('precipitation' in value) {
      title.push(
        <div key={index}>
          observation: {value.datetime}, precipitation:{' '}
          {value.precipitation?.toFixed(PRECIP_VALUES_DECIMAL)} mm
        </div>
      )
    }
  })
  return (
    <ToolTip title={title} aria-label="precipitation" arrow>
      <div className={precipitationClassName}>
        {precipitation &&
          typeof precipitation.precipitation === 'number' &&
          `${precipitation.precipitation.toFixed(PRECIP_VALUES_DECIMAL)} mm`}
      </div>
    </ToolTip>
  )
}

const formatDewPoint = (dewpoint: number | null | undefined) => {
  return (
    <div>
      {typeof dewpoint === 'number' &&
        `${dewpoint.toFixed(DEW_POINT_VALUES_DECIMAL)}${String.fromCharCode(176)}C`}
    </div>
  )
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
                return (
                  <TableRow data-testid={`comparison-table-row-${idx}`} key={idx}>
                    <TableCell>
                      {station?.properties.name} ({stationCode})
                    </TableCell>
                    {/* Temperature */}
                    <TableCell
                      data-testid="temperature-observation"
                      className={classes.darkColumn}
                    >
                      {formatTemperature(observation)}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatTemperature(noonForecast)}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatModelTemperature(hrdpsModelPrediction)}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatModelTemperature(rdpsModelPrediction)}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatModelTemperature(gdpsModelPrediction)}
                    </TableCell>
                    {/* Relative Humidity */}
                    <TableCell className={classes.lightColumn}>
                      {formatRelativeHumidity(observation, classes.relativeHumidityValue)}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatRelativeHumidity(
                        noonForecast,
                        classes.relativeHumidityValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatModelRelativeHumidity(
                        hrdpsModelPrediction,
                        classes.relativeHumidityValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatModelRelativeHumidity(
                        rdpsModelPrediction,
                        classes.relativeHumidityValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatModelRelativeHumidity(
                        gdpsModelPrediction,
                        classes.relativeHumidityValue
                      )}
                    </TableCell>
                    {/* Wind Speed + Direction */}
                    <TableCell className={classes.darkColumn}>
                      {formatWindSpeedDirection(
                        observation,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatWindSpeedDirection(
                        noonForecast,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatModelWindSpeedDirection(
                        hrdpsModelPrediction,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatModelWindSpeedDirection(
                        rdpsModelPrediction,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatModelWindSpeedDirection(
                        gdpsModelPrediction,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )}
                    </TableCell>
                    {/* Precip */}
                    <TableCell className={classes.lightColumn}>
                      {formatAccumulatedPrecipitation(
                        accumulatedObservedPrecipitation,
                        classes.precipitationValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatPrecipitation(
                        noonForecast?.total_precipitation,
                        classes.precipitationValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatAccumulatedPrecipitation(
                        accumulatedHRDPSPrecipitation,
                        classes.precipitationValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatAccumulatedPrecipitation(
                        accumulatedRDPSPrecipitation,
                        classes.precipitationValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatAccumulatedPrecipitation(
                        accumulatedGDPSPrecipitation,
                        classes.precipitationValue
                      )}
                    </TableCell>
                    {/* Dew Point */}
                    <TableCell
                      className={classes.darkColumn}
                      data-testid="dewpoint-observation"
                    >
                      {formatDewPoint(observation?.dewpoint)}
                    </TableCell>
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

export default React.memo(StationComparisonTable)
