import { LinearProgress } from '@mui/material'
import { styled } from '@mui/material/styles'
import {
  DataGridPro,
  GRID_TREE_DATA_GROUPING_FIELD,
  type GridCallbackDetails,
  type GridCellParams,
  type GridColDef,
  type GridColumnGroupingModel,
  type GridColumnVisibilityModel,
  type GridEventListener,
  type GridGroupingColDefOverride,
  type GridGroupNode,
  type GridRowHeightParams,
  type GridRowParams,
  GridTreeDataGroupingCell,
  type MuiEvent,
  useGridApiRef
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
  getForecastTreePath,
  getModelElevationCellValue,
  isModelElevationRow,
  type ModelElevationData
} from 'features/moreCast2/modelElevation'
import React, { useCallback, useEffect, useMemo } from 'react'

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
  styles['& .modelElevationRow .MuiDataGrid-cell'] = {
    borderTop: `1px solid ${theme.palette.divider}`,
    backgroundColor: theme.palette.grey[100]
  }
  styles['& .modelElevationRow .MuiDataGrid-treeDataGroupingCell'] = {
    width: '100%',
    minWidth: 0,
    alignItems: 'center'
  }
  styles['& .modelElevationRow .MuiDataGrid-treeDataGroupingCell > span'] = {
    minWidth: 0,
    flex: 1
  }

  return styles
})

export interface ForecastDataGridProps {
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
  collapsedStationCodes: Set<number>
  onStationExpansionChange: (stationCode: number, expanded: boolean) => void
  modelElevationData: ModelElevationData
  processRowUpdate: (newRow: MoreCast2Row) => MoreCast2Row
}

const LoadingOverlay = () => <LinearProgress />

const groupingColDef: GridGroupingColDefOverride<ForecastDisplayRow> = {
  headerName: 'Station',
  width: 200,
  minWidth: 200,
  sortable: false,
  disableColumnMenu: true,
  renderCell: params => {
    if (!isModelElevationRow(params.row) || params.rowNode.type !== 'group') return null
    return (
      <GridTreeDataGroupingCell
        {...params}
        rowNode={params.rowNode}
        hideDescendantCount
        formattedValue={
          <ModelElevationCell
            row={params.row}
            field="stationName"
            value={params.row.stationName}
            hasFocus={params.hasFocus}
          />
        }
      />
    )
  }
}

const gridSlots = { loadingOverlay: LoadingOverlay }
const gridInitialState = { pinnedColumns: { left: [GRID_TREE_DATA_GROUPING_FIELD, 'forDate'] } }
const getRowHeight = ({ model }: GridRowHeightParams) => (isModelElevationRow(model) ? 44 : null)
const getRowClassName = ({ row }: GridRowParams<ForecastDisplayRow>) =>
  isModelElevationRow(row) ? 'modelElevationRow' : ''
const isRowSelectable = ({ row }: GridRowParams<ForecastDisplayRow>) => !isModelElevationRow(row)
const getCellClassName = ({ row, field }: GridCellParams<ForecastDisplayRow>) => {
  if (isModelElevationRow(row)) return ''
  return field.endsWith('Forecast') || field.endsWith('Actual') ? 'forecastCell' : ''
}
const isCellEditable = (params: GridCellParams<ForecastDisplayRow>) =>
  params.colDef.editable === true &&
  !isModelElevationRow(params.row) &&
  params.row[params.field as keyof MoreCast2Row] !== ModelChoice.ACTUAL

const ForecastDataGrid = ({
  loading,
  columnClickHandlerProps,
  columnVisibilityModel,
  setColumnVisibilityModel,
  onCellDoubleClickHandler,
  handleColumnHeaderClick,
  columnGroupingModel,
  allMoreCast2Rows,
  collapsedStationCodes,
  onStationExpansionChange,
  modelElevationData,
  processRowUpdate
}: ForecastDataGridProps) => {
  // refs
  const apiRef = useGridApiRef()

  // derived data
  const displayRows = useMemo(
    () => getForecastDisplayRows(allMoreCast2Rows, modelElevationData.stationElevations),
    [allMoreCast2Rows, modelElevationData.stationElevations]
  )

  const sectionColumnGroupingModel = useMemo(
    () =>
      columnGroupingModel.map(group =>
        group.groupId === 'ID'
          ? { ...group, children: [{ field: GRID_TREE_DATA_GROUPING_FIELD }, { field: 'forDate' }] }
          : group
      ),
    [columnGroupingModel]
  )

  // keep metadata handling at the grid boundary so forecast renderers only see weather rows
  const columns = useMemo<GridColDef<ForecastDisplayRow>[]>(
    () =>
      DataGridColumns.getTabColumns(columnClickHandlerProps)
        .filter(column => column.field !== 'stationName')
        .map(column => {
          const model = weatherModelsWithTooltips.find(model => model === column.headerName)
          return {
            ...column,
            renderHeader: model
              ? params => (
                  <ModelHeader params={params} modelRunTimestamp={modelElevationData.latestRuns[model] ?? null} />
                )
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
                  />
                )
              }
              return column.renderCell ? column.renderCell(params) : params.formattedValue
            }
          }
        }),
    [columnClickHandlerProps, modelElevationData.latestRuns]
  )

  // callbacks
  const isGroupExpandedByDefault = useCallback(
    (node: GridGroupNode) => !collapsedStationCodes.has(Number(node.groupingKey)),
    [collapsedStationCodes]
  )

  const handleGridHeaderClick: GridEventListener<'columnHeaderClick'> = useCallback(
    (params, event, details) => {
      if (params.field !== GRID_TREE_DATA_GROUPING_FIELD) handleColumnHeaderClick(params, event, details)
    },
    [handleColumnHeaderClick]
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

  // effects
  useEffect(
    () =>
      apiRef.current?.subscribeEvent('rowExpansionChange', node => {
        onStationExpansionChange(Number(node.groupingKey), node.childrenExpanded ?? false)
      }),
    [apiRef, onStationExpansionChange]
  )

  // render
  return (
    <Root className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGridPro<ForecastDisplayRow>
        apiRef={apiRef}
        nonce={CSP_NONCE}
        treeData
        getTreeDataPath={getForecastTreePath}
        groupingColDef={groupingColDef}
        isGroupExpandedByDefault={isGroupExpandedByDefault}
        getCellClassName={getCellClassName}
        columnVisibilityModel={columnVisibilityModel}
        onColumnVisibilityModelChange={setColumnVisibilityModel}
        columnGroupingModel={sectionColumnGroupingModel}
        slots={gridSlots}
        onColumnHeaderClick={handleGridHeaderClick}
        onCellDoubleClick={handleGridDoubleClick}
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
