import React, { ReactElement } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import TableCell from '@material-ui/core/TableCell'
import TableRow from '@material-ui/core/TableRow'
import ToolTip from '@material-ui/core/Tooltip'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ObservedValue } from 'api/observationAPI'
import {
  DEW_POINT_VALUES_DECIMAL,
  PRECIP_VALUES_DECIMAL,
  RH_VALUES_DECIMAL,
  TEMPERATURE_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL,
  WIND_SPEED_FORECAST_VALUES_DECIMAL,
  WIND_DIRECTION_VALUES_DECIMAL
} from 'utils/constants'
import { AccumulatedPrecipitation } from 'utils/table'

export type DataSource = 'Observed' | 'Forecast' | 'HRDPS' | 'RDPS' | 'GDPS'

export type WeatherVariable =
  | 'Temperature'
  | 'Relative Humidity'
  | 'Wind Speed'
  | 'Wind Direction'
  | 'Precipitation'
  | 'Dew point'

interface CellFormattingInfo {
  formatFn: (source: any, valueClassName: string[]) => ReactElement | void
  data:
    | NoonForecastValue
    | ObservedValue
    | ModelValue
    | AccumulatedPrecipitation
    | number
    | undefined
  styling: string[]
}

interface Props {
  index: ReactElement
  headers: WeatherVariable[]
  subheaders: DataSource[][]
  forecast?: NoonForecastValue
  observation?: ObservedValue
  accumulatedObsPrecip?: AccumulatedPrecipitation
  highResModel?: ModelValue
  accumulatedHRDPSPrecip?: AccumulatedPrecipitation
  regionalModel?: ModelValue
  accumulatedRDPSPrecip?: AccumulatedPrecipitation
  globalModel?: ModelValue
  accumulatedGDPSPrecip?: AccumulatedPrecipitation
  testId?: string
  testIdRowNumber?: number
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
  darkColumn: {
    backgroundColor: '#fafafa',
    padding: '2px',
    paddingRight: '6px',
    textAlign: 'right'
  },
  lightColumn: {
    textAlign: 'right',
    padding: '2px',
    paddingRight: '6px'
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

const formatWindSpeedForecast = (
  source: NoonForecastValue | undefined,
  valueClassName: string[]
): ReactElement => {
  return (
    <div>
      {typeof source?.wind_speed === 'number' && (
        <div className={valueClassName[0]}>
          {source?.wind_speed?.toFixed(WIND_SPEED_FORECAST_VALUES_DECIMAL)}
        </div>
      )}
    </div>
  )
}

const formatWindSpeed = (
  source: ObservedValue | ModelValue | undefined,
  valueClassName: string[]
): ReactElement => {
  return (
    <div>
      {typeof source?.wind_speed === 'number' && (
        <div className={valueClassName[0]}>
          {source?.wind_speed?.toFixed(WIND_SPEED_VALUES_DECIMAL)}
        </div>
      )}
    </div>
  )
}

const formatWindDirection = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  valueClassName: string[]
): ReactElement => {
  return (
    <div>
      {typeof source?.wind_direction === 'number' && (
        <div className={valueClassName[0]}>
          {source?.wind_direction
            ?.toFixed(WIND_DIRECTION_VALUES_DECIMAL)
            .padStart(3, '0')}
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
        `${source?.temperature?.toFixed(TEMPERATURE_VALUES_DECIMAL)}`}
    </div>
  )
}

const formatRelativeHumidity = (
  source: NoonForecastValue | ObservedValue | ModelValue | undefined,
  valueClassName: string[]
): ReactElement => {
  return (
    <div className={valueClassName[0]}>
      {typeof source?.relative_humidity === 'number' &&
        `${source?.relative_humidity?.toFixed(RH_VALUES_DECIMAL)}`}
    </div>
  )
}

const formatPrecipitation = (
  precipitation: number | null | undefined,
  valueClassName: string[]
): ReactElement => {
  return (
    <div className={valueClassName[0]}>
      {typeof precipitation === 'number' &&
        `${precipitation.toFixed(PRECIP_VALUES_DECIMAL)}`}
    </div>
  )
}

const formatDewPoint = (observation: ObservedValue | undefined) => {
  const dewpoint = observation?.dewpoint
  return (
    <div>
      {typeof dewpoint === 'number' && `${dewpoint.toFixed(DEW_POINT_VALUES_DECIMAL)}`}
    </div>
  )
}

const formatModelTemperature = (source: ModelValue): ReactElement => {
  if (source === undefined) {
    return <div></div>
  }
  const tooltip = source.model_run_datetime
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
  valueClassName: string[]
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
  precipitationClassName: string[]
): ReactElement => {
  const title: JSX.Element[] = []
  precipitation?.values.forEach((value, index) => {
    if ('delta_precipitation' in value && 'model_run_datetime' in value) {
      title.push(
        <div key={index}>
          prediction: {value.datetime}, precipitation:{' '}
          {value.delta_precipitation?.toFixed(PRECIP_VALUES_DECIMAL)} (model:{' '}
          {value.model_run_datetime})
        </div>
      )
    } else if ('precipitation' in value) {
      title.push(
        <div key={index}>
          observation: {value.datetime}, precipitation:{' '}
          {value.precipitation?.toFixed(PRECIP_VALUES_DECIMAL)}
        </div>
      )
    }
  })
  return (
    <ToolTip title={title} aria-label="precipitation" arrow>
      <div className={precipitationClassName[0]}>
        {precipitation &&
          typeof precipitation.precipitation === 'number' &&
          `${precipitation.precipitation.toFixed(PRECIP_VALUES_DECIMAL)}`}
      </div>
    </ToolTip>
  )
}

const ComparisonTableRow = (props: Props) => {
  const classes = useStyles()

  const formattingMap: Record<WeatherVariable, Record<DataSource, CellFormattingInfo>> = {
    Temperature: {
      Observed: { formatFn: formatTemperature, data: props.observation, styling: [] },
      Forecast: { formatFn: formatTemperature, data: props.forecast, styling: [] },
      HRDPS: { formatFn: formatModelTemperature, data: props.highResModel, styling: [] },
      RDPS: { formatFn: formatModelTemperature, data: props.regionalModel, styling: [] },
      GDPS: { formatFn: formatModelTemperature, data: props.globalModel, styling: [] }
    },
    'Relative Humidity': {
      Observed: {
        formatFn: formatRelativeHumidity,
        data: props.observation,
        styling: [classes.relativeHumidityValue]
      },
      Forecast: {
        formatFn: formatRelativeHumidity,
        data: props.forecast,
        styling: [classes.relativeHumidityValue]
      },
      HRDPS: {
        formatFn: formatModelRelativeHumidity,
        data: props.highResModel,
        styling: [classes.relativeHumidityValue]
      },
      RDPS: {
        formatFn: formatModelRelativeHumidity,
        data: props.regionalModel,
        styling: [classes.relativeHumidityValue]
      },
      GDPS: {
        formatFn: formatModelRelativeHumidity,
        data: props.globalModel,
        styling: [classes.relativeHumidityValue]
      }
    },
    'Wind Speed': {
      Observed: {
        formatFn: formatWindSpeed,
        data: props.observation,
        styling: [classes.windSpeedValue]
      },
      Forecast: {
        formatFn: formatWindSpeedForecast,
        data: props.forecast,
        styling: [classes.windSpeedValue]
      },
      HRDPS: {
        formatFn: formatWindSpeed,
        data: props.highResModel,
        styling: [classes.windSpeedValue]
      },
      RDPS: {
        formatFn: formatWindSpeed,
        data: props.regionalModel,
        styling: [classes.windSpeedValue]
      },
      GDPS: {
        formatFn: formatWindSpeed,
        data: props.globalModel,
        styling: [classes.windSpeedValue]
      }
    },
    'Wind Direction': {
      Observed: {
        formatFn: formatWindDirection,
        data: props.observation,
        styling: [classes.windDirectionValue]
      },
      Forecast: {
        formatFn: formatWindDirection,
        data: props.forecast,
        styling: [classes.windDirectionValue]
      },
      HRDPS: {
        formatFn: formatWindDirection,
        data: props.highResModel,
        styling: [classes.windDirectionValue]
      },
      RDPS: {
        formatFn: formatWindDirection,
        data: props.regionalModel,
        styling: [classes.windDirectionValue]
      },
      GDPS: {
        formatFn: formatWindDirection,
        data: props.globalModel,
        styling: [classes.windDirectionValue]
      }
    },
    Precipitation: {
      Observed: {
        formatFn: formatAccumulatedPrecipitation,
        data: props.accumulatedObsPrecip,
        styling: [classes.precipitationValue]
      },
      Forecast: {
        formatFn: formatPrecipitation,
        data: props.forecast?.total_precipitation,
        styling: [classes.precipitationValue]
      },
      HRDPS: {
        formatFn: formatAccumulatedPrecipitation,
        data: props.accumulatedHRDPSPrecip,
        styling: [classes.precipitationValue]
      },
      RDPS: {
        formatFn: formatAccumulatedPrecipitation,
        data: props.accumulatedRDPSPrecip,
        styling: [classes.precipitationValue]
      },
      GDPS: {
        formatFn: formatAccumulatedPrecipitation,
        data: props.accumulatedGDPSPrecip,
        styling: [classes.precipitationValue]
      }
    },
    'Dew point': {
      Observed: { formatFn: formatDewPoint, data: props.observation, styling: [] },
      Forecast: { formatFn: () => undefined, data: undefined, styling: [] },
      HRDPS: { formatFn: () => undefined, data: undefined, styling: [] },
      RDPS: { formatFn: () => undefined, data: undefined, styling: [] },
      GDPS: { formatFn: () => undefined, data: undefined, styling: [] }
    }
  }

  return (
    <TableRow data-testid={`${props.testId}-${props.testIdRowNumber}`}>
      {props.index}
      {props.headers.map((variable: WeatherVariable, idx: number) => {
        const colStyle = idx % 2 === 0 ? classes.darkColumn : classes.lightColumn
        return props.subheaders[idx].map((source: DataSource) => {
          const formattingInfo = formattingMap[variable][source]
          const cellContent = formattingInfo.formatFn(
            formattingInfo.data,
            formattingInfo.styling
          )

          if (cellContent instanceof Object) {
            return (
              <TableCell
                className={colStyle}
                data-testid={`${props.testIdRowNumber}-${variable
                  .split(' ')
                  .join('-')}-${source}`}
                key={`${variable}-${source}`}
              >
                {cellContent}
              </TableCell>
            )
          } else {
            return null
          }
        })
      })}
    </TableRow>
  )
}

export default React.memo(ComparisonTableRow)
