import React from 'react'
import { styled } from '@mui/material/styles'
import { DataGridPro, GridCellParams, GridEventListener } from '@mui/x-data-grid-pro'
import { ModelChoice } from 'api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { LinearProgress } from '@mui/material'
import { DataGridColumns, getSummaryColumnGroupModel } from 'features/moreCast2/components/DataGridColumns'
import { MORECAST_WEATHER_PARAMS, MoreCastParams, theme } from 'app/theme'
import { MORECAST2_INDEX_FIELDS } from 'features/moreCast2/components/MoreCast2Column'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import { PINNED_COLUMNS } from 'features/moreCast2/components/ColumnDefBuilder'

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
  loading: boolean
  rows: MoreCast2Row[]
  columnClickHandlerProps: ColumnClickHandlerProps
  handleColumnHeaderClick: GridEventListener<'columnHeaderClick'>
  processRowUpdate: (newRow: MoreCast2Row) => MoreCast2Row
}

const ForecastSummaryDataGrid = ({
  loading,
  rows,
  columnClickHandlerProps,
  handleColumnHeaderClick,
  processRowUpdate
}: ForecastSummaryDataGridProps) => {
  const isCellEditable = (params: GridCellParams) => {
    // Actual fields and FWI fields (containing the 'Calc' substring) are not editable.
    return params.row[params.field] !== ModelChoice.ACTUAL && !params.field.includes('Calc')
  }

  return (
    <Root className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGridPro
        getCellClassName={params => {
          return params.field.endsWith('Forecast') || params.field.endsWith('Actual') ? 'forecastCell' : ''
        }}
        slots={{
          loadingOverlay: LinearProgress
        }}
        initialState={{
          sorting: {
            sortModel: [{ field: 'stationName', sort: 'asc' }]
          },
          pinnedColumns: { left: PINNED_COLUMNS }
        }}
        experimentalFeatures={{ columnGrouping: true }}
        columnGroupingModel={getSummaryColumnGroupModel()}
        onColumnHeaderClick={handleColumnHeaderClick}
        loading={loading}
        columns={DataGridColumns.getSummaryColumns(columnClickHandlerProps)}
        rows={rows}
        isCellEditable={isCellEditable}
        processRowUpdate={processRowUpdate}
      />
    </Root>
  )
}

export default ForecastSummaryDataGrid
