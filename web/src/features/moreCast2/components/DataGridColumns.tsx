import { GridColumnVisibilityModel, GridColDef, GridColumnGroupingModel } from '@mui/x-data-grid'
import { MORECAST2_FIELDS } from 'features/moreCast2/components/MoreCast2Field'

export interface ColumnVis {
  columnName: string
  visible: boolean
}

let columns: GridColDef[] = []
MORECAST2_FIELDS.forEach(field => {
  columns = [...columns, ...field.generateColDefs()]
})

export class DataGridColumns {
  public static initGridColumnVisibilityModel() {
    const model: GridColumnVisibilityModel = {}
    const weatherParameterColumns = getWeatherParameterColumns()
    weatherParameterColumns.forEach(columnName => {
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

  public static getColumns(): GridColDef[] {
    return columns
  }

  public static getWeatherParameterColumns() {
    const fields = columns.map(column => column.field)
    return fields.filter(field => field !== 'stationName' && field !== 'forDate')
  }
}

export const getWeatherParameterColumns = (): string[] => {
  const fields = columns.map(column => column.field)
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
      { field: 'windSpeedGFS' }
    ]
  }
]
