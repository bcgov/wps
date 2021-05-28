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
  WIND_SPEED_VALUES_DECIMAL
} from 'utils/constants'
import { AccumulatedPrecipitation } from 'utils/table'

export enum DataSource {
  'Observed',
  'Forecast',
  'HRDPS',
  'RDPS',
  'GDPS'
}

export enum WeatherVariable {
  'Temperature',
  'Relative Humidity',
  'Wind Speed + Direction',
  'Precipitation',
  'Dew point'
}

interface CellFormattingInfo {
  formatFn: (source: any, valueClassName?: string, windSpeedClassName?: string, windDirectionClassName?: string) => ReactElement
    // formatFn: object
  data:
    | NoonForecastValue
    | ObservedValue
    | ModelValue
    | AccumulatedPrecipitation
    | undefined
  styling?: string[]
}

interface Props {
  index: ReactElement
  headers: WeatherVariable[]
  subheaders: DataSource[][]
  forecast?: NoonForecastValue | undefined
  observation?: ObservedValue | undefined
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

  const formattingMap: Record<WeatherVariable, Record<DataSource, CellFormattingInfo>> = {
    0: {
      0: { formatFn: formatTemperature, data: props.observation },
      1: { formatFn: formatTemperature, data: props.forecast },
      2: { formatFn: formatModelTemperature, data: props.highResModel },
      3: { formatFn: formatModelTemperature, data: props.regionalModel },
      4: { formatFn: formatModelTemperature, data: props.globalModel }
    },
    1: {
      0: {
        formatFn: formatRelativeHumidity,
        data: props.observation,
        styling: [classes.relativeHumidityValue]
      },
      1: {
        formatFn: formatRelativeHumidity,
        data: props.forecast,
        styling: [classes.relativeHumidityValue]
      },
      2: {
        formatFn: formatModelRelativeHumidity,
        data: props.highResModel,
        styling: [classes.relativeHumidityValue]
      },
      3: {
        formatFn: formatModelRelativeHumidity,
        data: props.regionalModel,
        styling: [classes.relativeHumidityValue]
      },
      4: {
        formatFn: formatModelRelativeHumidity,
        data: props.globalModel,
        styling: [classes.relativeHumidityValue]
      }
    },
    2: {
      0: {
        formatFn: formatWindSpeedDirection,
        data: props.observation,
        styling: [classes.windSpeedValue, classes.windDirectionValue]
      },
      1: {
        formatFn: formatWindSpeedDirection,
        data: props.forecast,
        styling: [classes.windSpeedValue, classes.windDirectionValue]
      },
      2: {
        formatFn: formatWindSpeedDirection,
        data: props.highResModel,
        styling: [classes.windSpeedValue, classes.windDirectionValue]
      },
      3: {
        formatFn: formatWindSpeedDirection,
        data: props.regionalModel,
        styling: [classes.windSpeedValue, classes.windDirectionValue]
      },
      4: {
        formatFn: formatWindSpeedDirection,
        data: props.globalModel,
        styling: [classes.windSpeedValue, classes.windDirectionValue]
      }
    },
    3: {
      0: {
        formatFn: formatAccumulatedPrecipitation,
        data: props.accumulatedObsPrecip,
        styling: [classes.precipitationValue]
      },
      1: {
        formatFn: formatPrecipitation,
        data: props.forecast,
        styling: [classes.precipitationValue]
      },
      2: {
        formatFn: formatAccumulatedPrecipitation,
        data: props.accumulatedHRDPSPrecip,
        styling: [classes.precipitationValue]
      },
      3: {
        formatFn: formatAccumulatedPrecipitation,
        data: props.accumulatedRDPSPrecip,
        styling: [classes.precipitationValue]
      },
      4: {
        formatFn: formatAccumulatedPrecipitation,
        data: props.accumulatedGDPSPrecip,
        styling: [classes.precipitationValue]
      }
    },
    4: {
      0: { formatFn: formatDewPoint, data: props.observation },
      1: { formatFn: {}, data: undefined },
      2: { formatFn: {}, data: undefined },
      3: { formatFn: {}, data: undefined },
      4: { formatFn: {}, data: undefined }
    }
  }

  return (
    <TableRow data-testid={`${props.testId}-${props.testIdRowNumber}`}>
      {props.index}
      {props.headers.map((variable: WeatherVariable, idx: number) => {
        const colStyle = idx % 2 === 0 ? classes.darkColumn : classes.lightColumn
        return props.subheaders[idx].map((source: DataSource) => {
          const formattingInfo = formattingMap[variable][source]
          const bleh = formattingInfo.formatFn
          bleh(formattingInfo.data)
          const cellContent = formattingInfo.formatFn(formattingInfo.data, formattingInfo.styling)

          return (
            <TableCell
              className={colStyle}
              data-testid={`${props.testIdRowNumber}-${WeatherVariable[variable]
                .split(' ')
                .join('-')}-${DataSource[source]}`}
              key={`${variable}-${source}`}
            >
              {cellContent}
            </TableCell>
          )
        })
      })}
    </TableRow>
  )
}

export default React.memo(ComparisonTableRow)
