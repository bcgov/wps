import { GridColumnVisibilityModel, GridColDef, GridColumnGroupingModel } from '@mui/x-data-grid'
import { WeatherDeterminate } from 'api/moreCast2API'
import {
  MORECAST2_FIELDS,
  MORECAST2_FORECAST_FIELDS,
  MORECAST2_STATION_DATE_FIELDS
} from 'features/moreCast2/components/MoreCast2Column'

export interface ColumnVis {
  columnName: string
  visible: boolean
}

export class DataGridColumns {
  public static initGridColumnVisibilityModel() {
    const model: GridColumnVisibilityModel = {}
    const weatherParameterColumns = getWeatherParameterColumns()
    weatherParameterColumns.forEach(columnName => {
      // temperature columns are visible by default
      if (columnName.startsWith('temp')) {
        model[columnName] = true
      } else {
        model[columnName] = false
      }
    })
    return model
  }

  public static updateGridColumnVisibliityModel(
    parameters: ColumnVis[],
    columnVisibilityModel: GridColumnVisibilityModel
  ) {
    const newModel: GridColumnVisibilityModel = {}
    Object.assign(newModel, columnVisibilityModel)

    for (const property in columnVisibilityModel) {
      parameters.forEach(parameter => {
        if (property.startsWith(parameter.columnName)) {
          newModel[property] = parameter.visible
        }
      })
    }
    return newModel
  }

  public static getTabColumns(): GridColDef[] {
    let tabColumns: GridColDef[] = []
    MORECAST2_FIELDS.forEach(field => {
      tabColumns = [...tabColumns, ...field.generateColDefs(WeatherDeterminate.FORECAST)]
    })
    return tabColumns
  }

  public static getSummaryColumns(): GridColDef[] {
    return MORECAST2_STATION_DATE_FIELDS.map(field => field.generateColDef()).concat(
      MORECAST2_FORECAST_FIELDS.map(forecastField => forecastField.generateForecastColDef())
    )
  }

  public static getWeatherParameterColumns() {
    const fields = DataGridColumns.getTabColumns().map(column => column.field)
    return fields.filter(field => field !== 'stationName' && field !== 'forDate')
  }
}

export const getWeatherParameterColumns = (): string[] => {
  const fields = DataGridColumns.getTabColumns().map(column => column.field)
  return fields.filter(field => field !== 'stationName' && field !== 'forDate')
}

export const columnGroupingModel: GridColumnGroupingModel = [
  {
    groupId: 'ID',
    children: [{ field: 'stationName' }, { field: 'forDate' }]
  },
  {
    groupId: 'Temp',
    children: [
      { field: 'tempForecast' },
      { field: 'tempActual' },
      { field: 'tempHRDPS' },
      { field: 'tempRDPS' },
      { field: 'tempGDPS' },
      { field: 'tempNAM' },
      { field: 'tempGFS' }
    ]
  },
  {
    groupId: 'RH',
    children: [
      { field: 'rhForecast' },
      { field: 'rhActual' },
      { field: 'rhHRDPS' },
      { field: 'rhRDPS' },
      { field: 'rhGDPS' },
      { field: 'rhNAM' },
      { field: 'rhGFS' }
    ]
  },
  {
    groupId: 'Precip',
    children: [
      { field: 'precipForecast' },
      { field: 'precipActual' },
      { field: 'precipHRDPS' },
      { field: 'precipRDPS' },
      { field: 'precipGDPS' },
      { field: 'precipNAM' },
      { field: 'precipGFS' }
    ]
  },
  {
    groupId: 'Wind Dir',
    children: [
      { field: 'windDirectionForecast' },
      { field: 'windDirectionActual' },
      { field: 'windDirectionHRDPS' },
      { field: 'windDirectionRDPS' },
      { field: 'windDirectionGDPS' },
      { field: 'windDirectionNAM' },
      { field: 'windDirectionGFS' }
    ]
  },
  {
    groupId: 'Wind Speed',
    children: [
      { field: 'windSpeedForecast' },
      { field: 'windSpeedActual' },
      { field: 'windSpeedHRDPS' },
      { field: 'windSpeedRDPS' },
      { field: 'windSpeedGDPS' },
      { field: 'windSpeedNAM' },
      { field: 'windSpeedGFS' }
    ]
  }
]
