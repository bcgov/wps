import { LinearProgress } from '@mui/material'
import { alpha, styled } from '@mui/material/styles'
import {
  DataGridPro,
  type GridCallbackDetails,
  type GridCellParams,
  type GridColDef,
  type GridColumnGroupingModel,
  type GridColumnVisibilityModel,
  type GridEventListener,
  type GridRowHeightParams,
  type GridRowParams,
  type MuiEvent
} from '@mui/x-data-grid-pro'
import { ModelChoice, weatherModelsWithTooltips } from '@wps/api/moreCast2API'
import {
  MORECAST_MODEL_COLORS,
  MORECAST_WEATHER_PARAMS,
  type MoreCastModelColors,
  type MoreCastParams
} from '@wps/ui/theme'
import { CSP_NONCE } from '@wps/utils/env'
import { DataGridColumns } from 'features/moreCast2/components/DataGridColumns'
import ModelElevationCell from 'features/moreCast2/components/ModelElevationCell'
import ModelHeader from 'features/moreCast2/components/ModelHeader'
import type { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import type { MoreCast2Row } from 'features/moreCast2/interfaces'
import {
  type ForecastDisplayRow,
  getForecastDisplayRows,
  getModelElevationCellValue,
  isModelElevationRow,
  type ModelElevationData
} from 'features/moreCast2/modelElevation'
import React, { useCallback, useMemo } from 'react'
import { isForecastRow } from '../util'

const PREFIX = 'ForecastDataGrid'

const classes = {
  root: `${PREFIX}-root`
}

const Root = styled('div')(({ theme }) => {
  const styles: Record<string, React.CSSProperties> = {
    [`&.${classes.root}`]: {
      display: 'flex',
      flexGrow: 1,
      flexDirection: 'column',
      height: '1px'
    }
  }

  Object.keys(MORECAST_WEATHER_PARAMS).forEach(key => {
    styles[`& .MuiDataGrid-columnHeader.${key}`] = {
      backgroundColor: MORECAST_WEATHER_PARAMS[key as keyof MoreCastParams].active
    }
  })

  Object.keys(MORECAST_MODEL_COLORS).forEach(key => {
    styles[`& .MuiDataGrid-cell.${key}`] = {
      backgroundColor: MORECAST_MODEL_COLORS[key as keyof MoreCastModelColors].bg,
      borderRight: 'solid',
      borderWidth: '1px',
      // Ugly override, tried to avoid, but MUI overwrites border with it's own otherwise
      borderRightColor: `${MORECAST_MODEL_COLORS[key as keyof MoreCastModelColors].border} !important`
    }
    styles[`& .MuiDataGrid-columnHeader.${key}-header`] = {
      backgroundColor: MORECAST_MODEL_COLORS[key as keyof MoreCastModelColors].bg,
      borderBottom: 'solid',
      borderRight: 'solid',
      borderWidth: '1px',

      // Ugly override, tried to avoid, but MUI overwrites border with it's own otherwise
      borderColor: `${MORECAST_MODEL_COLORS[key as keyof MoreCastModelColors].border} !important`
    }
  })

  styles[`& .forecastCell`] = {
    backgroundColor: 'rgba(238,238,238,1)'
  }
  styles['& .actualCell'] = {
    backgroundColor: alpha(theme.palette.primary.main, 0.06)
  }
  styles['& .MuiDataGrid-columnHeader[data-field$="Actual"]'] = {
    backgroundColor: alpha(theme.palette.primary.main, 0.12)
  }

  styles['& .modelElevationRow .MuiDataGrid-cell'] = {
    borderTop: `1px solid ${theme.palette.divider}`,
    backgroundColor: theme.palette.grey[100]
  }

  return styles
})

export interface ForecastDataGridProps {
  onForecastStationChange?: (stationCode: number) => void
  loading: boolean
  columnClickHandlerProps: ColumnClickHandlerProps
  columnVisibilityModel: GridColumnVisibilityModel
  setColumnVisibilityModel: React.Dispatch<React.SetStateAction<GridColumnVisibilityModel>>
  onCellDoubleClickHandler: (
    params: GridCellParams,
    event: MuiEvent<React.MouseEvent>,
    details: GridCallbackDetails
  ) => void
  handleColumnHeaderClick: GridEventListener<'columnHeaderClick'>
  columnGroupingModel: GridColumnGroupingModel
  allMoreCast2Rows: MoreCast2Row[]
  modelElevationData: ModelElevationData
  onCompareElevations: (stationCode: number) => void
  processRowUpdate: (newRow: MoreCast2Row) => MoreCast2Row
}

const LoadingOverlay = () => <LinearProgress />

// grid configuration
const gridSlots = { loadingOverlay: LoadingOverlay }
const gridInitialState = { pinnedColumns: { left: ['stationName', 'forDate'] } }

// row rules
const getRowHeight = ({ model }: GridRowHeightParams) => (isModelElevationRow(model) ? 44 : null)
const getRowClassName = ({ row }: GridRowParams<ForecastDisplayRow>) =>
  isModelElevationRow(row) ? 'modelElevationRow' : ''
const isRowSelectable = ({ row }: GridRowParams<ForecastDisplayRow>) => !isModelElevationRow(row)

// cell rules
const getCellClassName = ({ row, field }: GridCellParams<ForecastDisplayRow>) => {
  if (isModelElevationRow(row)) return ''
  if (field.endsWith('Actual')) return 'actualCell'
  return field.endsWith('Forecast') ? 'forecastCell' : ''
}

const isCellEditable = (params: GridCellParams<ForecastDisplayRow>) =>
  params.colDef.editable === true &&
  !isModelElevationRow(params.row) &&
  params.row[params.field as keyof MoreCast2Row] !== ModelChoice.ACTUAL

// elevation rows bypass weather getters and formatters because they contain station metadata
const addElevationRowSupport = (
  column: GridColDef,
  latestRuns: ModelElevationData['latestRuns'],
  onCompareElevations: ForecastDataGridProps['onCompareElevations']
): GridColDef<ForecastDisplayRow> => {
  const model = weatherModelsWithTooltips.find(model => model === column.headerName)

  return {
    ...column,
    renderHeader: model
      ? params => <ModelHeader params={params} modelRunTimestamp={latestRuns[model] ?? null} />
      : column.renderHeader,
    valueGetter: (value, row, colDef, apiRef) => {
      if (isModelElevationRow(row)) return getModelElevationCellValue(row, column.field, column.headerName)

      return column.valueGetter ? column.valueGetter(value, row, colDef, apiRef) : value
    },
    valueFormatter: (value, row, colDef, apiRef) => {
      if (isModelElevationRow(row)) return value

      return column.valueFormatter ? column.valueFormatter(value, row, colDef, apiRef) : value
    },
    renderCell: params => {
      if (isModelElevationRow(params.row)) {
        return (
          <ModelElevationCell
            row={params.row}
            field={params.field}
            value={String(params.formattedValue ?? '')}
            model={model}
            hasFocus={params.hasFocus}
            onCompareElevations={column.field === 'stationName' ? onCompareElevations : undefined}
          />
        )
      }

      if (column.field === 'stationName') return null
      return column.renderCell ? column.renderCell(params) : params.formattedValue
    }
  }
}

const ForecastDataGrid = ({
  loading,
  columnClickHandlerProps,
  columnVisibilityModel,
  setColumnVisibilityModel,
  onCellDoubleClickHandler,
  handleColumnHeaderClick,
  columnGroupingModel,
  allMoreCast2Rows,
  modelElevationData,
  onCompareElevations,
  onForecastStationChange,
  processRowUpdate
}: ForecastDataGridProps) => {
  // derived data
  const displayRows = useMemo(
    () => getForecastDisplayRows(allMoreCast2Rows, modelElevationData.stationElevations),
    [allMoreCast2Rows, modelElevationData.stationElevations]
  )

  const columns = useMemo(
    () =>
      DataGridColumns.getTabColumns(columnClickHandlerProps).map(column =>
        addElevationRowSupport(column, modelElevationData.latestRuns, onCompareElevations)
      ),
    [columnClickHandlerProps, modelElevationData.latestRuns, onCompareElevations]
  )

  // callbacks
  const handleGridCellClick: GridEventListener<'cellClick'> = useCallback(
    params => {
      if (!isModelElevationRow(params.row) && isForecastRow(params.row)) {
        onForecastStationChange?.(params.row.stationCode)
      }
    },
    [onForecastStationChange]
  )

  const handleGridDoubleClick: ForecastDataGridProps['onCellDoubleClickHandler'] = useCallback(
    (params, event, details) => {
      if (isModelElevationRow(params.row)) {
        event.defaultMuiPrevented = true
        return
      }
      onCellDoubleClickHandler(params, event, details)
    },
    [onCellDoubleClickHandler]
  )

  const updateGridRow = useCallback(
    (newRow: ForecastDisplayRow, oldRow: ForecastDisplayRow) =>
      isModelElevationRow(newRow) ? oldRow : processRowUpdate(newRow),
    [processRowUpdate]
  )

  // render
  return (
    <Root className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGridPro<ForecastDisplayRow>
        nonce={CSP_NONCE}
        getCellClassName={getCellClassName}
        columnVisibilityModel={columnVisibilityModel}
        onColumnVisibilityModelChange={setColumnVisibilityModel}
        columnGroupingModel={columnGroupingModel}
        columnGroupHeaderHeight={36}
        columnHeaderHeight={44}
        slots={gridSlots}
        onColumnHeaderClick={handleColumnHeaderClick}
        onCellDoubleClick={handleGridDoubleClick}
        onCellClick={handleGridCellClick}
        loading={loading}
        columns={columns}
        getRowClassName={getRowClassName}
        getRowHeight={getRowHeight}
        isRowSelectable={isRowSelectable}
        isCellEditable={isCellEditable}
        rows={displayRows}
        processRowUpdate={updateGridRow}
        initialState={gridInitialState}
        hideFooter={true}
      />
    </Root>
  )
}

export default React.memo(ForecastDataGrid)
