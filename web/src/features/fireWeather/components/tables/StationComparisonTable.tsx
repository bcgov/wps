import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import Paper from '@material-ui/core/Paper'
import Typography from '@material-ui/core/Typography'
import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import TableHead from '@material-ui/core/TableHead'
// import TableSortLabel from '@material-ui/core/TableSortLabel'
import { GeoJsonStation } from 'api/stationAPI'
import { ObservedValue } from 'api/observationAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ModelValue } from 'api/modelAPI'
import { getNoonDate, formatDateInPST, reformatDate } from 'utils/date'
import {
  TEMPERATURE_VALUES_DECIMAL,
  RH_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL,
  PRECIP_VALUES_DECIMAL,
  DEW_POINT_VALUES_DECIMAL
} from 'utils/constants'

const useStyles = makeStyles({
  paper: {
    padding: '5px'
  },
  typography: {},
  tableContainer: {
    // '& .MuiTableCell-sizeSmall': {
    //   padding: '1px',
    //   textAlign: 'right'
    // }
  },
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
    padding: '1px',
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
  noonModelsByStation: Record<number, ModelValue[] | undefined>
}

const findNoonMatch = (
  noonDate: string,
  collection: ModelValue[] | undefined
): ModelValue | undefined => {
  return collection?.find((item: ModelValue) => reformatDate(item.datetime) === noonDate)
}

const formatTemperature = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined
) => {
  return (
    source && (
      <div>
        {typeof source?.temperature === 'number' &&
          `${source?.temperature?.toFixed(
            TEMPERATURE_VALUES_DECIMAL
          )}${String.fromCharCode(176)}C`}
      </div>
    )
  )
}

const formatRelativeHumidity = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  valueClassName: any
) => {
  return (
    source && (
      <div className={valueClassName}>
        {typeof source?.relative_humidity === 'number' &&
          `${source?.relative_humidity?.toFixed(RH_VALUES_DECIMAL)}%`}
      </div>
    )
  )
}

const formatWindSpeedDirection = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  windSpeedClassName: any,
  windDirectionClassName: any
) => {
  return (
    source && (
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
  )
}

const formatPrecipitation = (
  precipitation: number | null | undefined,
  precipitationClassName: any
) => {
  return (
    <div className={precipitationClassName}>
      {typeof precipitation === 'number' &&
        `${precipitation.toFixed(PRECIP_VALUES_DECIMAL)} mm`}
    </div>
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

const StationComparisonTable = (props: Props) => {
  const classes = useStyles()
  const noonDate = getNoonDate(props.timeOfInterest)
  return (
    <Paper className={classes.paper}>
      <Typography className={classes.typography} component="div" variant="subtitle2">
        Station comparison for {formatDateInPST(noonDate)} PDT
      </Typography>
      <Paper>
        <TableContainer className={classes.tableContainer}>
          <Table stickyHeader size="small" aria-label="sortable wx table">
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
                {/* Temperature */}
                <TableCell className={classes.darkColumnHeader}>Observed</TableCell>
                <TableCell className={classes.darkColumnHeader}>Forecast</TableCell>
                <TableCell className={classes.darkColumnHeader}>HRDPS</TableCell>
                <TableCell className={classes.darkColumnHeader}>RDPS</TableCell>
                <TableCell className={classes.darkColumnHeader}>GDPS</TableCell>
                {/* Relative Humidity */}
                <TableCell className={classes.lightColumnHeader}>Observed</TableCell>
                <TableCell className={classes.lightColumnHeader}>Forecast</TableCell>
                <TableCell className={classes.lightColumnHeader}>HRDPS</TableCell>
                <TableCell className={classes.lightColumnHeader}>RDPS</TableCell>
                <TableCell className={classes.lightColumnHeader}>GDPS</TableCell>
                {/* Wind Speed + Direction */}
                <TableCell className={classes.darkColumnHeader}>Observed</TableCell>
                <TableCell className={classes.darkColumnHeader}>Forecast</TableCell>
                <TableCell className={classes.darkColumnHeader}>HRDPS</TableCell>
                <TableCell className={classes.darkColumnHeader}>RDPS</TableCell>
                <TableCell className={classes.darkColumnHeader}>GDPS</TableCell>
                {/* Precip */}
                <TableCell className={classes.lightColumnHeader}>Observed</TableCell>
                <TableCell className={classes.lightColumnHeader}>Forecast</TableCell>
                <TableCell className={classes.lightColumnHeader}>HRDPS</TableCell>
                <TableCell className={classes.lightColumnHeader}>RDPS</TableCell>
                <TableCell className={classes.lightColumnHeader}>GDPS</TableCell>
                {/* Dew Point */}
                <TableCell className={classes.darkColumnHeader}>Observed</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {props.stationCodes.map((stationCode: number, idx: number) => {
                const station = props.stationsByCode[stationCode]
                const noonForecasts = props.allNoonForecastsByStation[stationCode]
                const noonForecast = noonForecasts?.find(
                  forecast => reformatDate(forecast.datetime) === noonDate
                )
                const observations = props.observationsByStation[stationCode]
                const observation = observations?.find(
                  observation => reformatDate(observation.datetime) === noonDate
                )
                const hrdpsModelPrediction = findNoonMatch(
                  noonDate,
                  props.allHighResModelsByStation[stationCode]
                )
                const rdpsModelPrediction = findNoonMatch(
                  noonDate,
                  props.allRegionalModelsByStation[stationCode]
                )
                const gdpsModelPrediction = findNoonMatch(
                  noonDate,
                  props.noonModelsByStation[stationCode]
                )
                return (
                  <TableRow key={idx}>
                    <TableCell>
                      {station?.properties.name} ({stationCode})
                    </TableCell>
                    {/* Temperature */}
                    <TableCell className={classes.darkColumn}>
                      {formatTemperature(observation)}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatTemperature(noonForecast)}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatTemperature(hrdpsModelPrediction)}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatTemperature(rdpsModelPrediction)}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatTemperature(gdpsModelPrediction)}
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
                      {formatRelativeHumidity(
                        hrdpsModelPrediction,
                        classes.relativeHumidityValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatRelativeHumidity(
                        rdpsModelPrediction,
                        classes.relativeHumidityValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatRelativeHumidity(
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
                      {formatWindSpeedDirection(
                        hrdpsModelPrediction,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatWindSpeedDirection(
                        rdpsModelPrediction,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )}
                    </TableCell>
                    <TableCell className={classes.darkColumn}>
                      {formatWindSpeedDirection(
                        gdpsModelPrediction,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )}
                    </TableCell>
                    {/* Precip */}
                    <TableCell className={classes.lightColumn}>
                      {formatPrecipitation(
                        observation?.precipitation,
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
                      {formatPrecipitation(
                        hrdpsModelPrediction?.delta_precipitation,
                        classes.precipitationValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatPrecipitation(
                        rdpsModelPrediction?.delta_precipitation,
                        classes.precipitationValue
                      )}
                    </TableCell>
                    <TableCell className={classes.lightColumn}>
                      {formatPrecipitation(
                        gdpsModelPrediction?.delta_precipitation,
                        classes.precipitationValue
                      )}
                    </TableCell>
                    {/* Dew Point */}
                    <TableCell className={classes.darkColumn}>
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
