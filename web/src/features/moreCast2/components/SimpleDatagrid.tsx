import React from 'react'
import { styled } from '@mui/material/styles'
import { DataGridPro, GridEventListener } from '@mui/x-data-grid-pro'
import { ModelChoice } from 'api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { LinearProgress } from '@mui/material'
import { DataGridColumns, getSummaryColumnGroupModel } from 'features/moreCast2/components/DataGridColumns'
import { getSimulatedIndicesAndStoreEditedRows } from 'features/moreCast2/slices/dataSlice'
import { AppDispatch } from 'app/store'
import { useDispatch } from 'react-redux'
import { fillStationGrassCuringForward } from 'features/moreCast2/util'
import { MORECAST_WEATHER_PARAMS, MoreCastParams, theme } from 'app/theme'
import { MORECAST2_INDEX_FIELDS } from 'features/moreCast2/components/MoreCast2Column'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import { PINNED_COLUMNS } from 'features/moreCast2/components/ColumnDefBuilder'

const PREFIX = 'SimpleDataGrid'

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

interface SimpleDataGridProps {
  loading: boolean
  rows: MoreCast2Row[]
  columnClickHandlerProps: ColumnClickHandlerProps
  handleColumnHeaderClick: GridEventListener<'columnHeaderClick'>
}

const SimpleDataGrid = ({ loading, rows, columnClickHandlerProps, handleColumnHeaderClick }: SimpleDataGridProps) => {
  const dispatch: AppDispatch = useDispatch()

  const processRowUpdate = async (newRow: MoreCast2Row) => {
    const filledRows = fillStationGrassCuringForward(newRow, rows)

    dispatch(getSimulatedIndicesAndStoreEditedRows(newRow, filledRows))

    return newRow
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
        isCellEditable={params => params.row[params.field] !== ModelChoice.ACTUAL}
        processRowUpdate={processRowUpdate}
      />
    </Root>
  )
}

export default SimpleDataGrid
