import React, { ReactElement } from 'react'
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
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ObservedValue } from 'api/observationAPI'
import { GeoJsonStation } from 'api/stationAPI'
import {
  DEW_POINT_VALUES_DECIMAL,
  PRECIP_VALUES_DECIMAL,
  RH_VALUES_DECIMAL,
  TEMPERATURE_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL
} from 'utils/constants'
import { AccumulatedPrecipitation, calculateAccumulatedPrecip } from 'utils/table'

enum DataSource {
  Observed,
  Forecast,
  HRDPS,
  RDPS,
  GDPS
}

enum WeatherVariable {
  'Temperature',
  'Relative Humidity',
  'Wind Speed + Direction',
  'Precipitation',
  'Dew point'
}

interface Props {
  headers: WeatherVariable[]
  subheaders: [DataSource[]]
  forecast?: NoonForecastValue | undefined
  observation?: ObservedValue | undefined
  highResModel?: ModelValue
  accumulatedHRDPSPrecip?: AccumulatedPrecipitation
  regionalModel?: ModelValue
  accumulatedRDPSPrecip?: AccumulatedPrecipitation
  globalModel?: ModelValue
  accumulatedGDPSPrecip?: AccumulatedPrecipitation
}

const useStyles = makeStyles({
  paper: {
    width: '100%'
  },
  lightColumnHeader: {
    textAlign: 'center',
    padding: '2px',
    minWidth: '60px'
  },
  darkColumnHeader: {
    backgroundColor: 'rgb(240, 240, 240)',
    textAlign: 'center',
    padding: '2px',
    minWidth: '60px'
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

const formatWindSpeedDirection = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  windSpeedClassName: string,
  windDirectionClassName: string
): ReactElement => {
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

const formatTemperature = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined
): ReactElement => {
  return (
    <div>
      {typeof source?.temperature === 'number' &&
        `${source?.temperature?.toFixed(TEMPERATURE_VALUES_DECIMAL)}${String.fromCharCode(
          176
        )}C`}
    </div>
  )
}

const formatRelativeHumidity = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  valueClassName: string
): ReactElement => {
  return (
    <div className={valueClassName}>
      {typeof source?.relative_humidity === 'number' &&
        `${source?.relative_humidity?.toFixed(RH_VALUES_DECIMAL)}%`}
    </div>
  )
}

const formatPrecipitation = (
  precipitation: number | null | undefined,
  precipitationClassName: string
): ReactElement => {
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

const formatModelTemperature = (source: ModelValue): ReactElement => {
  const tooltip = (source as ModelValue).model_run_datetime
  return (
    source && (
      <ToolTip title={`model run time: ${tooltip}`} aria-label="temperature" arrow>
        {formatTemperature(source)}
      </ToolTip>
    )
  )
}

const formatModelRelativeHumidity = (
  source: ModelValue | undefined,
  valueClassName: string
): ReactElement => {
  const tooltip = (source as ModelValue)?.model_run_datetime
  return (
    <ToolTip title={`model run time: ${tooltip}`} aria-label="Relative humidity" arrow>
      {formatRelativeHumidity(source, valueClassName)}
    </ToolTip>
  )
}

const formatAccumulatedPrecipitation = (
  precipitation: AccumulatedPrecipitation,
  precipitationClassName: string
): ReactElement => {
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

const ComparisonTableRow = (props: Props) => {
  const classes = useStyles()

  return (
    <TableRow>
      {props.headers.map((variable: WeatherVariable, idx: number) => {
        {
          let cellContent: ReactElement

          props.subheaders[idx].map((source: DataSource) => {
            switch (source) {
              case DataSource.Observed: {
                switch (variable) {
                  case WeatherVariable.Temperature: {
                    cellContent = formatTemperature(props.observation)
                    break
                  }
                  case WeatherVariable['Relative Humidity']: {
                    cellContent = formatRelativeHumidity(
                      props.observation,
                      classes.relativeHumidityValue
                    )
                    break
                  }
                  case WeatherVariable.Precipitation: {
                    cellContent = formatPrecipitation(
                      props.observation?.precipitation,
                      classes.precipitationValue
                    )
                    break
                  }
                  case WeatherVariable['Dew point']: {
                    cellContent = formatDewPoint(props.observation?.dewpoint)
                    break
                  }
                  case WeatherVariable['Wind Speed + Direction']: {
                    cellContent = formatWindSpeedDirection(
                      props.observation,
                      classes.windSpeedValue,
                      classes.windDirectionValue
                    )
                    break
                  }
                }
                break
              }
              case DataSource.Forecast: {
                switch (variable) {
                  case WeatherVariable.Temperature: {
                    cellContent = formatTemperature(props.forecast)
                    break
                  }
                  case WeatherVariable['Relative Humidity']: {
                    cellContent = formatRelativeHumidity(
                      props.forecast,
                      classes.relativeHumidityValue
                    )
                    break
                  }
                  case WeatherVariable.Precipitation: {
                    cellContent = formatPrecipitation(
                      props.forecast?.total_precipitation,
                      classes.precipitationValue
                    )
                    break
                  }
                  case WeatherVariable['Wind Speed + Direction']: {
                    cellContent = formatWindSpeedDirection(
                      props.forecast,
                      classes.windSpeedValue,
                      classes.windDirectionValue
                    )
                    break
                  }
                }
                break
              }
              case DataSource.HRDPS: {
                switch (variable) {
                  case WeatherVariable.Temperature: {
                    if (props.highResModel && props.highResModel !== undefined) {
                      cellContent = formatModelTemperature(props.highResModel)
                    }
                    break
                  }
                  case WeatherVariable['Relative Humidity']: {
                    if (props.highResModel && props.highResModel !== undefined) {
                      cellContent = formatModelRelativeHumidity(
                        props.highResModel,
                        classes.relativeHumidityValue
                      )
                    }
                    break
                  }
                  case WeatherVariable.Precipitation: {
                    if (props.accumulatedHRDPSPrecip && props.accumulatedHRDPSPrecip !== undefined) {
                      cellContent = formatAccumulatedPrecipitation(
                        props.accumulatedHRDPSPrecip,
                        classes.precipitationValue
                      )
                    }
                    break
                  }
                  case WeatherVariable['Wind Speed + Direction']: {
                    if (props.highResModel && props.highResModel !== undefined) {
                      cellContent = formatWindSpeedDirection(
                        props.highResModel,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )
                    }
                    break
                  }
                }
                break
              }
              case DataSource.RDPS: {
                switch (variable) {
                  case WeatherVariable.Temperature: {
                    if (props.regionalModel && props.regionalModel !== undefined) {
                      cellContent = formatTemperature(props.regionalModel)
                    }
                    break
                  }
                  case WeatherVariable['Relative Humidity']: {
                    if (props.regionalModel && props.regionalModel !== undefined) {
                      cellContent = formatModelRelativeHumidity(
                        props.regionalModel,
                        classes.relativeHumidityValue
                      )
                    }
                    break
                  }
                  case WeatherVariable.Precipitation: {
                      if(props.accumulatedRDPSPrecip && props.accumulatedRDPSPrecip !== undefined) {
                          cellContent = formatAccumulatedPrecipitation(props.accumulatedRDPSPrecip, classes.precipitationValue)
                      }
                    break
                  }
                  case WeatherVariable['Wind Speed + Direction']: {
                    if (props.regionalModel && props.regionalModel !== undefined) {
                      cellContent = formatWindSpeedDirection(
                        props.regionalModel,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )
                    }
                    break
                  }
                }
                break
              }
              case DataSource.GDPS: {
                switch (variable) {
                  case WeatherVariable.Temperature: {
                    if (props.globalModel && props.globalModel !== undefined) {
                      cellContent = formatTemperature(props.globalModel)
                    }
                    break
                  }
                  case WeatherVariable['Relative Humidity']: {
                    if (props.globalModel && props.globalModel !== undefined) {
                      cellContent = formatModelRelativeHumidity(
                        props.globalModel,
                        classes.relativeHumidityValue
                      )
                    }
                    break
                  }
                  case WeatherVariable.Precipitation: {
                      if (props.accumulatedGDPSPrecip && props.accumulatedGDPSPrecip !== undefined) {
                          cellContent = formatAccumulatedPrecipitation(props.accumulatedGDPSPrecip, classes.precipitationValue)
                      }
                    break
                  }
                  case WeatherVariable['Wind Speed + Direction']: {
                    if (props.globalModel && props.globalModel !== undefined) {
                      cellContent = formatWindSpeedDirection(
                        props.globalModel,
                        classes.windSpeedValue,
                        classes.windDirectionValue
                      )
                    }
                    break
                  }
                }
                break
              }
            }
            return <TableCell>{cellContent}</TableCell>
          })
        }
      })}
    </TableRow>
  )
}

export default React.memo(ComparisonTableRow)
