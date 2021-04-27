import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
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
  container: {
    borderRadius: '4px',
    backgroundColor: 'white'
  },
  tableContainer: {},
  groupHeader: {
    textAlign: 'center'
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
    <div className={classes.container}>
      <Typography component="div" variant="subtitle2">
        Station comparison for {formatDateInPST(noonDate)} PDT
      </Typography>
      <TableContainer className={classes.tableContainer}>
        <Table stickyHeader size="small" aria-label="sortable wx table">
          <TableHead>
            <TableRow>
              <TableCell></TableCell>
              <TableCell className={classes.groupHeader} colSpan={5}>
                Temperature
              </TableCell>
              <TableCell className={classes.groupHeader} colSpan={5}>
                Relative Humidity
              </TableCell>
              <TableCell className={classes.groupHeader} colSpan={5}>
                Wind Speed + Direction
              </TableCell>
              <TableCell className={classes.groupHeader} colSpan={5}>
                Precipitation
              </TableCell>
              <TableCell className={classes.groupHeader}>Dew point</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Weather Stations</TableCell>
              {/* Temperature */}
              <TableCell>Observed</TableCell>
              <TableCell>Forecast</TableCell>
              <TableCell>HRDPS</TableCell>
              <TableCell>RDPS</TableCell>
              <TableCell>GDPS</TableCell>
              {/* Relative Humidity */}
              <TableCell>Observed</TableCell>
              <TableCell>Forecast</TableCell>
              <TableCell>HRDPS</TableCell>
              <TableCell>RDPS</TableCell>
              <TableCell>GDPS</TableCell>
              {/* Wind Speed + Direction */}
              <TableCell>Observed</TableCell>
              <TableCell>Forecast</TableCell>
              <TableCell>HRDPS</TableCell>
              <TableCell>RDPS</TableCell>
              <TableCell>GDPS</TableCell>
              {/* Precip */}
              <TableCell>Observed</TableCell>
              <TableCell>Forecast</TableCell>
              <TableCell>HRDPS</TableCell>
              <TableCell>RDPS</TableCell>
              <TableCell>GDPS</TableCell>
              {/* Dew Point */}
              <TableCell>Observed</TableCell>
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
                  <TableCell>{formatTemperature(observation)}</TableCell>
                  <TableCell>{formatTemperature(noonForecast)}</TableCell>
                  <TableCell>{formatTemperature(hrdpsModelPrediction)}</TableCell>
                  <TableCell>{formatTemperature(rdpsModelPrediction)}</TableCell>
                  <TableCell>{formatTemperature(gdpsModelPrediction)}</TableCell>
                  {/* Relative Humidity */}
                  <TableCell>
                    {formatRelativeHumidity(observation, classes.relativeHumidityValue)}
                  </TableCell>
                  <TableCell>
                    {formatRelativeHumidity(noonForecast, classes.relativeHumidityValue)}
                  </TableCell>
                  <TableCell>
                    {formatRelativeHumidity(
                      hrdpsModelPrediction,
                      classes.relativeHumidityValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatRelativeHumidity(
                      rdpsModelPrediction,
                      classes.relativeHumidityValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatRelativeHumidity(
                      gdpsModelPrediction,
                      classes.relativeHumidityValue
                    )}
                  </TableCell>
                  {/* Wind Speed + Direction */}
                  <TableCell>
                    {formatWindSpeedDirection(
                      observation,
                      classes.windSpeedValue,
                      classes.windDirectionValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatWindSpeedDirection(
                      noonForecast,
                      classes.windSpeedValue,
                      classes.windDirectionValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatWindSpeedDirection(
                      hrdpsModelPrediction,
                      classes.windSpeedValue,
                      classes.windDirectionValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatWindSpeedDirection(
                      rdpsModelPrediction,
                      classes.windSpeedValue,
                      classes.windDirectionValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatWindSpeedDirection(
                      gdpsModelPrediction,
                      classes.windSpeedValue,
                      classes.windDirectionValue
                    )}
                  </TableCell>
                  {/* Precip */}
                  <TableCell>
                    {formatPrecipitation(
                      observation?.precipitation,
                      classes.precipitationValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatPrecipitation(
                      noonForecast?.total_precipitation,
                      classes.precipitationValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatPrecipitation(
                      hrdpsModelPrediction?.delta_precipitation,
                      classes.precipitationValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatPrecipitation(
                      rdpsModelPrediction?.delta_precipitation,
                      classes.precipitationValue
                    )}
                  </TableCell>
                  <TableCell>
                    {formatPrecipitation(
                      gdpsModelPrediction?.delta_precipitation,
                      classes.precipitationValue
                    )}
                  </TableCell>
                  {/* Dew Point */}
                  <TableCell>{formatDewPoint(observation?.dewpoint)}</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  )
}

export default React.memo(StationComparisonTable)
