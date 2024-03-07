import React from 'react'
import { Typography } from '@mui/material'
import { GridColumnVisibilityModel, GridColDef, GridColumnGroup } from '@mui/x-data-grid'
import { WeatherDeterminate, WeatherDeterminateChoices } from 'api/moreCast2API'
import {
  MORECAST2_FIELDS,
  MORECAST2_FORECAST_FIELDS,
  MORECAST2_INDEX_FIELDS,
  MORECAST2_STATION_DATE_FIELDS,
  MORECAST2_GRASS_CURING_CWFIS_FIELD,
  MORECAST2_GRASS_CURING_FORECAST_FIELD
} from 'features/moreCast2/components/MoreCast2Column'
import GroupHeader from 'features/moreCast2/components/GroupHeader'
import { handleShowHideChangeType } from 'features/moreCast2/components/TabbedDataGrid'
import { MoreCastParams } from 'app/theme'

export interface ColumnVis {
  columnName: string
  displayName?: string
  visible: boolean
}

export class DataGridColumns {
  public static initGridColumnVisibilityModel() {
    // First check local storage for existing column visibility
    const groupedColumnVisibility = localStorage.getItem('groupedColumnVisibility')
    if (groupedColumnVisibility) {
      console.log(groupedColumnVisibility)
    }

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

  public static updateGridColumnVisibilityModel(
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

  public static updateGridColumnVisibilityFromShowHideColumnsModel(
    parameters: ColumnVis[],
    columnVisibilityModel: GridColumnVisibilityModel
  ) {
    const newModel: GridColumnVisibilityModel = {}
    Object.assign(newModel, columnVisibilityModel)
    for (const param of parameters) {
      newModel[param.columnName] = param.visible
    }
    return newModel
  }

  public static getTabColumns(): GridColDef[] {
    let tabColumns: GridColDef[] = []
    MORECAST2_FIELDS.forEach(field => {
      tabColumns = [...tabColumns, ...field.generateColDefs(WeatherDeterminate.FORECAST)]
    })
    const gcForecastField = MORECAST2_GRASS_CURING_FORECAST_FIELD.generateForecastColDef()
    const gcCwfisField = MORECAST2_GRASS_CURING_CWFIS_FIELD.generateColDef()
    tabColumns.push(gcForecastField)
    tabColumns.push(gcCwfisField)

    return tabColumns
  }

  public static getSummaryColumns(): GridColDef[] {
    return MORECAST2_STATION_DATE_FIELDS.map(field => field.generateColDef()).concat(
      MORECAST2_FORECAST_FIELDS.map(forecastField => forecastField.generateForecastColDef()).concat(
        MORECAST2_INDEX_FIELDS.map(field => field.generateForecastColDef())
      )
    )
  }

  public static getWeatherParameterColumns() {
    const fields = DataGridColumns.getTabColumns().map(column => column.field)
    return fields.filter(field => field !== 'stationName' && field !== 'forDate')
  }

  public static getWeatherModelColumns() {
    const columns = DataGridColumns.getTabColumns()
    return columns.filter(
      column => column.field !== 'stationName' && column.field !== 'forDate' && !column.field.endsWith('Forecast')
    )
  }
}

const renderGroupHeader = (
  id: string,
  weatherParam: keyof MoreCastParams,
  columns?: ColumnVis[],
  handleShowHideChange?: handleShowHideChangeType
) => {
  return (
    <GroupHeader columns={columns} id={id} weatherParam={weatherParam} handleShowHideChange={handleShowHideChange} />
  )
}

export const getTabColumnGroupModel = (
  showHideColumnsModel?: Record<string, ColumnVis[]>,
  handleShowHideChange?: handleShowHideChangeType
): GridColumnGroup[] => {
  const model = [
    {
      groupId: 'ID',
      children: [{ field: 'stationName' }, { field: 'forDate' }],
      renderHeaderGroup: () => {
        return <Typography style={{ fontWeight: 'bold' }}>ID</Typography>
      }
    },
    {
      groupId: 'Temp',
      children: columnGroupingModelChildGenerator('temp'),
      headerClassName: 'temp',
      renderHeaderGroup: () =>
        renderGroupHeader('Temp', 'temp', showHideColumnsModel && showHideColumnsModel['temp'], handleShowHideChange)
    },
    {
      groupId: 'RH',
      children: columnGroupingModelChildGenerator('rh'),
      headerClassName: 'rh',
      renderHeaderGroup: () =>
        renderGroupHeader('RH', 'rh', showHideColumnsModel && showHideColumnsModel['rh'], handleShowHideChange)
    },
    {
      groupId: 'Precip',
      children: columnGroupingModelChildGenerator('precip'),
      headerClassName: 'precip',
      renderHeaderGroup: () =>
        renderGroupHeader(
          'Precip',
          'precip',
          showHideColumnsModel && showHideColumnsModel['precip'],
          handleShowHideChange
        )
    },
    {
      groupId: 'Wind Dir',
      children: columnGroupingModelChildGenerator('windDirection'),
      headerClassName: 'windDirection',
      renderHeaderGroup: () =>
        renderGroupHeader(
          'Wind Dir',
          'windDirection',
          showHideColumnsModel && showHideColumnsModel['windDirection'],
          handleShowHideChange
        )
    },
    {
      groupId: 'Wind Speed',
      children: columnGroupingModelChildGenerator('windSpeed'),
      headerClassName: 'windSpeed',
      renderHeaderGroup: () =>
        renderGroupHeader(
          'Wind Speed',
          'windSpeed',
          showHideColumnsModel && showHideColumnsModel['windSpeed'],
          handleShowHideChange
        )
    },
    {
      groupId: 'Grass Curing',
      children: [
        {
          groupId: 'Grass Curing Forecast',
          field: 'grassCuringForecast'
        },
        {
          groupId: 'Grass Curing CWFIS',
          field: 'grassCuringCWFIS'
        }
      ],
      headerClassName: 'gc',
      renderHeaderGroup: () => {
        return <Typography style={{ fontWeight: 'bold' }}>Grass Curing</Typography>
      }
    }
  ]
  return model
}

export const getSummaryColumnGroupModel = () => {
  // const model = getTabColumnGroupModel()
  const model = [
    {
      groupId: 'ID',
      children: [{ field: 'stationName' }, { field: 'forDate' }],
      renderHeaderGroup: () => {
        return <Typography style={{ fontWeight: 'bold' }}>ID</Typography>
      }
    },
    {
      groupId: 'Temp',
      children: columnGroupingModelChildGenerator('temp'),
      headerClassName: 'temp-forecast-header',
      renderHeaderGroup: () => renderGroupHeader('Temp', 'temp')
    },
    {
      groupId: 'RH',
      children: columnGroupingModelChildGenerator('rh'),
      headerClassName: 'rh-forecast-header',
      renderHeaderGroup: () => <Typography style={{ fontWeight: 'bold' }}>RH</Typography>
    },
    {
      groupId: 'Wind Dir',
      children: columnGroupingModelChildGenerator('windDirection'),
      headerClassName: 'windDirection-forecast-header',
      renderHeaderGroup: () => <Typography style={{ fontWeight: 'bold' }}>Wind Dir</Typography>
    },
    {
      groupId: 'Wind Speed',
      children: columnGroupingModelChildGenerator('windSpeed'),
      headerClassName: 'windSpeed-forecast-header',
      renderHeaderGroup: () => <Typography style={{ fontWeight: 'bold' }}>Wind Speed</Typography>
    },
    {
      groupId: 'Precip',
      children: columnGroupingModelChildGenerator('precip'),
      headerClassName: 'precip-forecast-header',
      renderHeaderGroup: () => <Typography style={{ fontWeight: 'bold' }}>Precip</Typography>
    },
    {
      groupId: 'GC',
      children: [
        {
          groupId: 'Grass Curing Forecast',
          field: 'grassCuringForecast'
        },
        {
          groupId: 'Grass Curing CWFIS',
          field: 'grassCuringCWFIS'
        }
      ],
      headerClassName: 'gc-forecast-header',
      renderHeaderGroup: () => {
        return <Typography style={{ fontWeight: 'bold' }}>GC</Typography>
      }
    },
    {
      groupId: 'FWI',
      children: [
        {
          groupId: 'FFMC',
          field: 'ffmcCalcForecast'
        },
        {
          groupId: 'DMC',
          field: 'dmcCalcForecast'
        },
        {
          groupId: 'DC',
          field: 'dcCalcForecast'
        },
        {
          groupId: 'ISI',
          field: 'isiCalcForecast'
        },
        {
          groupId: 'BUI',
          field: 'buiCalcForecast'
        },
        {
          groupId: 'FWI',
          field: 'fwiCalcForecast'
        },
        {
          groupId: 'DGR',
          field: 'dgrCalcForecast'
        }
      ],
      headerClassName: 'ffmcCalc-forecast-header',
      renderHeaderGroup: () => {
        return <Typography style={{ fontWeight: 'bold' }}>FWI</Typography>
      }
    }
  ]
  return model
}

// Returns an array of objects of the shape { field: weather parameter + weather determinate }. For example,
// eg. { field: 'tempACTUAL' }  These objects are used in the column grouping model to help manage grouping
// and visibility of our weather parameter tabs
function columnGroupingModelChildGenerator(weatherParam: string) {
  // For a given weather model, there are tabs present in the datagrid for each WeatherDetermiante except
  // WeatherDeterminate.NULL
  let determinates: WeatherDeterminate[] = []
  determinates = WeatherDeterminateChoices.filter(choice => choice !== WeatherDeterminate.NULL)
  const children = determinates.map(determinate => {
    return {
      field: `${weatherParam}${determinate}`
    }
  })
  return children
}
