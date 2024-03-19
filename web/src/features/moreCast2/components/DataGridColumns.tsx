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
import { ColumnClickHandlerProps, handleShowHideChangeType } from 'features/moreCast2/components/TabbedDataGrid'
import { MoreCastParams } from 'app/theme'

export interface ColumnVis {
  columnName: string
  displayName?: string
  visible: boolean
}

export class DataGridColumns {
  public static initGridColumnVisibilityModel(columnClickHandlerProps: ColumnClickHandlerProps) {
    // First check local storage for existing column visibility
    const groupedColumnVisibility = localStorage.getItem('groupedColumnVisibility')
    if (groupedColumnVisibility) {
      console.log(groupedColumnVisibility)
    }

    const model: GridColumnVisibilityModel = {}
    const weatherParameterColumns = this.getWeatherParameterColumns(columnClickHandlerProps)
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

  public static getTabColumns(columnClickHandlerProps: ColumnClickHandlerProps): GridColDef[] {
    let tabColumns: GridColDef[] = []
    MORECAST2_FIELDS.forEach(field => {
      tabColumns = [...tabColumns, ...field.generateColDefs(columnClickHandlerProps, WeatherDeterminate.FORECAST)]
    })
    const gcForecastField = MORECAST2_GRASS_CURING_FORECAST_FIELD.generateForecastColDef(columnClickHandlerProps)
    const gcCwfisField = MORECAST2_GRASS_CURING_CWFIS_FIELD.generateColDef(columnClickHandlerProps)
    tabColumns.push(gcForecastField)
    tabColumns.push(gcCwfisField)

    return tabColumns
  }

  public static getSummaryColumns(columnClickHandlerProps: ColumnClickHandlerProps): GridColDef[] {
    return MORECAST2_STATION_DATE_FIELDS.map(field => field.generateColDef(columnClickHandlerProps)).concat(
      MORECAST2_FORECAST_FIELDS.map(forecastField =>
        forecastField.generateForecastColDef(columnClickHandlerProps)
      ).concat(MORECAST2_INDEX_FIELDS.map(field => field.generateForecastColDef(columnClickHandlerProps)))
    )
  }

  public static getWeatherParameterColumns(columnClickHandlerProps: ColumnClickHandlerProps) {
    const fields = DataGridColumns.getTabColumns(columnClickHandlerProps).map(column => column.field)
    return fields.filter(field => field !== 'stationName' && field !== 'forDate')
  }

  public static getWeatherModelColumns(columnClickHandlerProps: ColumnClickHandlerProps) {
    const columns = DataGridColumns.getTabColumns(columnClickHandlerProps)
    return columns.filter(
      column => column.field !== 'stationName' && column.field !== 'forDate' && !column.field.endsWith('Forecast')
    )
  }
}

const renderSimpleGroupHeader = (id: string) => <Typography style={{ fontWeight: 'bold' }}>{id}</Typography>

const renderGroupHeader = (
  id: string,
  weatherParam: keyof MoreCastParams,
  columns: ColumnVis[],
  handleShowHideChange: handleShowHideChangeType
) => {
  return (
    <GroupHeader columns={columns} id={id} weatherParam={weatherParam} handleShowHideChange={handleShowHideChange} />
  )
}

export const getTabColumnGroupModel = (
  showHideColumnsModel: Record<string, ColumnVis[]>,
  handleShowHideChange: handleShowHideChangeType
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
      renderHeaderGroup: () => renderGroupHeader('Temp', 'temp', showHideColumnsModel['temp'], handleShowHideChange)
    },
    {
      groupId: 'RH',
      children: columnGroupingModelChildGenerator('rh'),
      headerClassName: 'rh',
      renderHeaderGroup: () => renderGroupHeader('RH', 'rh', showHideColumnsModel['rh'], handleShowHideChange)
    },
    {
      groupId: 'Precip',
      children: columnGroupingModelChildGenerator('precip'),
      headerClassName: 'precip',
      renderHeaderGroup: () =>
        renderGroupHeader('Precip', 'precip', showHideColumnsModel['precip'], handleShowHideChange)
    },
    {
      groupId: 'Wind Dir',
      children: columnGroupingModelChildGenerator('windDirection'),
      headerClassName: 'windDirection',
      renderHeaderGroup: () =>
        renderGroupHeader('Wind Dir', 'windDirection', showHideColumnsModel['windDirection'], handleShowHideChange)
    },
    {
      groupId: 'Wind Speed',
      children: columnGroupingModelChildGenerator('windSpeed'),
      headerClassName: 'windSpeed',
      renderHeaderGroup: () =>
        renderGroupHeader('Wind Speed', 'windSpeed', showHideColumnsModel['windSpeed'], handleShowHideChange)
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
  const model = [
    {
      groupId: 'ID',
      children: [{ field: 'stationName' }, { field: 'forDate' }],
      renderHeaderGroup: () => renderSimpleGroupHeader('ID')
    },
    {
      groupId: 'Temp',
      children: columnGroupingModelChildGenerator('temp'),
      headerClassName: 'temp-forecast-header',
      renderHeaderGroup: () => renderSimpleGroupHeader('Temp')
    },
    {
      groupId: 'RH',
      children: columnGroupingModelChildGenerator('rh'),
      headerClassName: 'rh-forecast-header',
      renderHeaderGroup: () => renderSimpleGroupHeader('RH')
    },
    {
      groupId: 'Wind Dir',
      children: columnGroupingModelChildGenerator('windDirection'),
      headerClassName: 'windDirection-forecast-header',
      renderHeaderGroup: () => renderSimpleGroupHeader('Wind Dir')
    },
    {
      groupId: 'Wind Speed',
      children: columnGroupingModelChildGenerator('windSpeed'),
      headerClassName: 'windSpeed-forecast-header',
      renderHeaderGroup: () => renderSimpleGroupHeader('Wind Speed')
    },
    {
      groupId: 'Precip',
      children: columnGroupingModelChildGenerator('precip'),
      headerClassName: 'precip-forecast-header',
      renderHeaderGroup: () => renderSimpleGroupHeader('Precip')
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
      renderHeaderGroup: () => renderSimpleGroupHeader('GC')
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
      renderHeaderGroup: () => renderSimpleGroupHeader('FWI')
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
