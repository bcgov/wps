import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
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
  WIND_SPEED_VALUES_DECIMAL
} from 'utils/constants'

const useStyles = makeStyles({
  tableContainer: {},
  groupHeader: {
    textAlign: 'center'
  },
  windSpeed: {
    whiteSpace: 'nowrap'
  },
  relativeHumidity: {
    whiteSpace: 'nowrap'
  },
  windDirection: {
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
        {source?.temperature?.toFixed(TEMPERATURE_VALUES_DECIMAL)}
        {source?.temperature && `${String.fromCharCode(176)}C`}
      </div>
    )
  )
}

const formatRelativeHumidity = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  relativeHumidity: any
) => {
  return (
    source && (
      <div className={relativeHumidity}>
        {source?.relative_humidity?.toFixed(RH_VALUES_DECIMAL)}
        {source?.relative_humidity && ' %rh'}
      </div>
    )
  )
}

const formatWindSpeedDirection = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  windSpeed: any,
  windDirection: any
) => {
  return (
    source && (
      <div>
        {source?.wind_speed && (
          <div className={windSpeed}>
            {source?.wind_speed?.toFixed(WIND_SPEED_VALUES_DECIMAL)} km/h
          </div>
        )}
        {source?.wind_speed && source?.wind_direction && ' '}
        {source?.wind_direction && (
          <div className={windDirection}>
            {source?.wind_direction?.toFixed(WIND_SPEED_VALUES_DECIMAL)}
            {source?.wind_direction && String.fromCharCode(176)}
          </div>
        )}
      </div>
    )
  )
}

const StationComparisonTable = (props: Props) => {
  const classes = useStyles()
  const noonDate = getNoonDate(props.timeOfInterest)
  return (
    <div>
      <div>Station comparison for {formatDateInPST(noonDate)} PDT</div>
      <TableContainer className={classes.tableContainer}>
        <Table stickyHeader size="small" aria-label="sortable wx table">
          <TableHead>
            <TableRow>
              <TableCell></TableCell>
              <TableCell className={classes.groupHeader} colSpan={5}>
                Temperature
              </TableCell>
              <TableCell colSpan={5}>Relative Humidity</TableCell>
              <TableCell colSpan={5}>Wind Speed + Direction</TableCell>
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
                    {formatRelativeHumidity(observation, classes.relativeHumidity)}
                  </TableCell>
                  <TableCell>
                    {formatRelativeHumidity(noonForecast, classes.relativeHumidity)}
                  </TableCell>
                  <TableCell>
                    {formatRelativeHumidity(
                      hrdpsModelPrediction,
                      classes.relativeHumidity
                    )}
                  </TableCell>
                  <TableCell>
                    {formatRelativeHumidity(
                      rdpsModelPrediction,
                      classes.relativeHumidity
                    )}
                  </TableCell>
                  <TableCell>
                    {formatRelativeHumidity(
                      gdpsModelPrediction,
                      classes.relativeHumidity
                    )}
                  </TableCell>
                  {/* Wind Speed + Direction */}
                  <TableCell>
                    {formatWindSpeedDirection(
                      observation,
                      classes.windSpeed,
                      classes.windDirection
                    )}
                  </TableCell>
                  <TableCell>
                    {formatWindSpeedDirection(
                      noonForecast,
                      classes.windSpeed,
                      classes.windDirection
                    )}
                  </TableCell>
                  <TableCell>
                    {formatWindSpeedDirection(
                      hrdpsModelPrediction,
                      classes.windSpeed,
                      classes.windDirection
                    )}
                  </TableCell>
                  <TableCell>
                    {formatWindSpeedDirection(
                      rdpsModelPrediction,
                      classes.windSpeed,
                      classes.windDirection
                    )}
                  </TableCell>
                  <TableCell>
                    {formatWindSpeedDirection(
                      gdpsModelPrediction,
                      classes.windSpeed,
                      classes.windDirection
                    )}
                  </TableCell>
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
