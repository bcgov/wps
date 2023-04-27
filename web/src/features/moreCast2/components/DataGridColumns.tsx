import { GridColumnVisibilityModel, GridColDef, GridColumnGroupingModel } from '@mui/x-data-grid'
import { WeatherDeterminate, WeatherDeterminateChoices } from 'api/moreCast2API'
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
    const weatherParameterColumns = this.getWeatherParameterColumns()
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
    children: columnGroupingModelChildGenerator('temp')
  },
  {
    groupId: 'RH',
    children: columnGroupingModelChildGenerator('rh')
  },
  {
    groupId: 'Precip',
    children: columnGroupingModelChildGenerator('precip')
  },
  {
    groupId: 'Wind Dir',
    children: columnGroupingModelChildGenerator('winDirection')
  },
  {
    groupId: 'Wind Speed',
    children: columnGroupingModelChildGenerator('windSpeed')
  }
]

// Returns an array of objects of the shape { field: weather parameter + weather determiante }. For example,
// eg. { field: 'tempACTUAL' }  This objects are used in the column grouping model to help manage grouping
// and visibility of our weather paramter tabs
function columnGroupingModelChildGenerator(weatherParam: string) {
  // For a given weather model, there are tabs present in the datagrid for each WeatherDetermiante except
  // WeatherDeterminate.NULL
  const determinates = WeatherDeterminateChoices.filter(choice => choice !== WeatherDeterminate.NULL)
  const children = determinates.map(determinate => {
    return {
      field: `${weatherParam}${determinate}`
    }
  })
  return children
}
