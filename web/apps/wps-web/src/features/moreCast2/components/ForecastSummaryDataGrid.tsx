import { LinearProgress } from '@mui/material'
import { styled } from '@mui/material/styles'
import { DataGridPro, type DataGridProProps, type GridCellParams, type GridEventListener } from '@mui/x-data-grid-pro'
import { ModelChoice } from '@wps/api/moreCast2API'
import { MORECAST_WEATHER_PARAMS, type MoreCastParams, theme } from '@wps/ui/theme'
import { CSP_NONCE } from '@wps/utils/env'
import { PINNED_COLUMNS } from 'features/moreCast2/components/ColumnDefBuilder'
import { DataGridColumns, getSummaryColumnGroupModel } from 'features/moreCast2/components/DataGridColumns'
import { MORECAST2_INDEX_FIELDS } from 'features/moreCast2/components/MoreCast2Column'
import type { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import type { MoreCast2Row } from 'features/moreCast2/interfaces'
import React, { useCallback, useMemo } from 'react'
import { isForecastRow } from '../util'

const PREFIX = 'ForecastSummaryDataGrid'

const classes = {
  root: `${PREFIX}-root`
}

const Root = styled('div')(() => {
  const styles: Record<string, React.CSSProperties> = {
    [`&.${classes.root}`]: {
      display: 'flex',
      flexGrow: 1,
      flexDirection: 'column',
      height: '1px'
    }
  }

  Object.keys(MORECAST_WEATHER_PARAMS).forEach(key => {
    styles[`& .${key}-forecast-header`] = {
      backgroundColor: `${MORECAST_WEATHER_PARAMS[key as keyof MoreCastParams].active}`
    }
  })

  MORECAST2_INDEX_FIELDS.forEach(indexField => {
    styles[`& .${indexField.getField()}-forecast-header`] = {
      backgroundColor: `rgba(0, 51, 102, 1)`,
      color: theme.palette.common.white
    }
  })

  styles[`& .forecastCell`] = {
    backgroundColor: 'rgba(238,238,238,1)'
  }

  return styles
})

interface ForecastSummaryDataGridProps {
  onForecastStationChange?: (stationCode: number) => void
  loading: boolean
  rows: MoreCast2Row[]
  columnClickHandlerProps: ColumnClickHandlerProps
  handleColumnHeaderClick: GridEventListener<'columnHeaderClick'>
  processRowUpdate: (newRow: MoreCast2Row) => MoreCast2Row
}

const LoadingOverlay = () => <LinearProgress />

// grid configuration
const slots = { loadingOverlay: LoadingOverlay }
const columnGroupingModel = getSummaryColumnGroupModel()
const initialState: DataGridProProps<MoreCast2Row>['initialState'] = {
  sorting: { sortModel: [{ field: 'stationName', sort: 'asc' }] },
  pinnedColumns: { left: PINNED_COLUMNS }
}

// cell rules
const getCellClassName = ({ field }: GridCellParams) =>
  field.endsWith('Forecast') || field.endsWith('Actual') ? 'forecastCell' : ''

const isCellEditable = (params: GridCellParams) => {
  // actual fields and calculated indices are not editable
  return params.row[params.field] !== ModelChoice.ACTUAL && !params.field.includes('Calc')
}

const ForecastSummaryDataGrid = ({
  onForecastStationChange,
  loading,
  rows,
  columnClickHandlerProps,
  handleColumnHeaderClick,
  processRowUpdate
}: ForecastSummaryDataGridProps) => {
  // derived data
  const columns = useMemo(() => DataGridColumns.getSummaryColumns(columnClickHandlerProps), [columnClickHandlerProps])

  // callbacks
  const handleGridCellClick: GridEventListener<'cellClick'> = useCallback(
    params => {
      if (isForecastRow(params.row)) onForecastStationChange?.(params.row.stationCode)
    },
    [onForecastStationChange]
  )

  // render
  return (
    <Root className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGridPro
        nonce={CSP_NONCE}
        getCellClassName={getCellClassName}
        slots={slots}
        initialState={initialState}
        columnGroupingModel={columnGroupingModel}
        columnGroupHeaderHeight={36}
        columnHeaderHeight={44}
        onColumnHeaderClick={handleColumnHeaderClick}
        onCellClick={handleGridCellClick}
        loading={loading}
        columns={columns}
        rows={rows}
        isCellEditable={isCellEditable}
        processRowUpdate={processRowUpdate}
        hideFooter={true}
      />
    </Root>
  )
}

export default React.memo(ForecastSummaryDataGrid)
