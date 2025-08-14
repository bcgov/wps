import React from 'react'
import { Typography, Tooltip, IconButton } from '@mui/material'
import { Info as InfoIcon } from '@mui/icons-material'
import { GridColumnVisibilityModel, GridColDef, GridColumnGroup, GridColumnHeaderParams } from '@mui/x-data-grid-pro'
import { WeatherDeterminate } from 'api/moreCast2API'
import { ORDERED_COLUMN_HEADERS } from 'features/moreCast2/components/ColumnDefBuilder'
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
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { DateTime } from 'luxon'
import { GridComponentRenderer } from '@/features/moreCast2/components/GridComponentRenderer'

export interface ColumnVis {
  columnName: string
  displayName?: string
  visible: boolean
}

export enum GroupHeaderName {
  GC = 'GC (%)',
  PRECIP = 'Precip (mm)',
  RH = 'RH (%)',
  TEMP = 'Temp (°C)',
  WindDir = 'Wind Direction (°)',
  WindSpeed = 'Wind Speed (km/h)'
}

export class DataGridColumns {
  public static initGridColumnVisibilityModel(
    columnClickHandlerProps: ColumnClickHandlerProps,
    allRows?: MoreCast2Row[]
  ) {
    const model: GridColumnVisibilityModel = {}
    const weatherParameterColumns = this.getWeatherParameterColumns(columnClickHandlerProps, allRows)
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

  public static getTabColumns(
    columnClickHandlerProps: ColumnClickHandlerProps,
    allRows?: MoreCast2Row[]
  ): GridColDef[] {
    let tabColumns: GridColDef[] = []
    MORECAST2_FIELDS.forEach(field => {
      tabColumns = [
        ...tabColumns,
        ...field.generateColDefs(columnClickHandlerProps, WeatherDeterminate.FORECAST, undefined, undefined, allRows)
      ]
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

  public static getWeatherParameterColumns(columnClickHandlerProps: ColumnClickHandlerProps, allRows?: MoreCast2Row[]) {
    const fields = DataGridColumns.getTabColumns(columnClickHandlerProps, allRows).map(column => column.field)
    return fields.filter(field => field !== 'stationName' && field !== 'forDate')
  }

  public static getWeatherModelColumns(columnClickHandlerProps: ColumnClickHandlerProps, allRows?: MoreCast2Row[]) {
    const columns = DataGridColumns.getTabColumns(columnClickHandlerProps, allRows)
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
  handleShowHideChange: handleShowHideChangeType,
  allRows?: MoreCast2Row[]
): GridColumnGroup[] => {
  const model = [
    {
      groupId: 'ID',
      children: [{ field: 'stationName' }, { field: 'forDate' }],
      renderHeaderGroup: () => renderSimpleGroupHeader('ID')
    },
    {
      groupId: 'Temp',
      children: columnGroupingModelChildGenerator('temp', allRows),
      headerClassName: 'temp',
      renderHeaderGroup: () =>
        renderGroupHeader(GroupHeaderName.TEMP, 'temp', showHideColumnsModel['temp'], handleShowHideChange)
    },
    {
      groupId: 'RH',
      children: columnGroupingModelChildGenerator('rh', allRows),
      headerClassName: 'rh',
      renderHeaderGroup: () =>
        renderGroupHeader(GroupHeaderName.RH, 'rh', showHideColumnsModel['rh'], handleShowHideChange)
    },
    {
      groupId: 'Precip',
      children: columnGroupingModelChildGenerator('precip', allRows),
      headerClassName: 'precip',
      renderHeaderGroup: () =>
        renderGroupHeader(GroupHeaderName.PRECIP, 'precip', showHideColumnsModel['precip'], handleShowHideChange)
    },
    {
      groupId: 'Wind Dir',
      children: columnGroupingModelChildGenerator('windDirection', allRows),
      headerClassName: 'windDirection',
      renderHeaderGroup: () =>
        renderGroupHeader(
          GroupHeaderName.WindDir,
          'windDirection',
          showHideColumnsModel['windDirection'],
          handleShowHideChange
        )
    },
    {
      groupId: 'Wind Speed',
      children: columnGroupingModelChildGenerator('windSpeed', allRows),
      headerClassName: 'windSpeed',
      renderHeaderGroup: () =>
        renderGroupHeader(
          GroupHeaderName.WindSpeed,
          'windSpeed',
          showHideColumnsModel['windSpeed'],
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
        return <Typography style={{ fontWeight: 'bold' }}>{GroupHeaderName.GC}</Typography>
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
function columnGroupingModelChildGenerator(weatherParam: string, allRows?: MoreCast2Row[]) {
  // Match the column creation pattern from ColumnDefBuilder.generateColDefs():
  // 1. First a Forecast column is created
  // 2. Then columns for each determinate in ORDERED_COLUMN_HEADERS are created
  const determinates = [WeatherDeterminate.FORECAST, ...ORDERED_COLUMN_HEADERS] as WeatherDeterminate[]

  const children = determinates.map(determinate => {
    const childGroup: any = {
      field: `${weatherParam}${determinate}`
    }

    // Add custom header rendering for weather model columns (not Actual or Forecast)
    // These should show tooltips for the weather models defined in ORDERED_COLUMN_HEADERS
    if (determinate !== WeatherDeterminate.ACTUAL && determinate !== WeatherDeterminate.FORECAST) {
      childGroup.renderHeaderGroup = () =>
        new GridComponentRenderer().renderHeaderWith(
          {
            field: `${weatherParam}${determinate}`,
            colDef: {
              field: `${weatherParam}${determinate}`
            }
          },
          allRows
        )
    }

    return childGroup
  })

  return children
}
