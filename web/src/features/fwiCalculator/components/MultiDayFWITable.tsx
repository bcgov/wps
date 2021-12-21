import {
  SelectionState,
  IntegratedSelection,
  IntegratedSorting,
  SortingState
} from '@devexpress/dx-react-grid'
import {
  ColumnChooser,
  Grid as ReactGrid,
  TableColumnVisibility,
  TableFixedColumns,
  TableHeaderRow,
  TableSelection,
  Toolbar,
  VirtualTable
} from '@devexpress/dx-react-grid-material-ui'
import { Paper } from '@material-ui/core'
import {
  defaultColumns,
  generateDefaultRowsFromDates
} from 'features/fwiCalculator/components/dataModel'
import React, { useState } from 'react'
import { getDaysBetween } from 'utils/date'

export interface MultiDayFWITableProps {
  startDate: string
  endDate: string
}

export const MultiDayFWITable = ({
  startDate,
  endDate
}: MultiDayFWITableProps): JSX.Element => {
  const [columns] = useState(defaultColumns)

  const [rightColumns] = useState([
    TableSelection.COLUMN_TYPE,
    'ffmc',
    TableSelection.COLUMN_TYPE,
    'dmc',
    TableSelection.COLUMN_TYPE,
    'dc',
    TableSelection.COLUMN_TYPE,
    'isi',
    TableSelection.COLUMN_TYPE,
    'bui',
    TableSelection.COLUMN_TYPE,
    'fwi'
  ])

  const [selection, setSelection] = useState<(string | number)[]>([])

  const dates = getDaysBetween(startDate, endDate)
  const genRows = generateDefaultRowsFromDates(dates)

  return (
    <Paper>
      <ReactGrid rows={genRows} columns={columns}>
        <SortingState defaultSorting={[{ columnName: 'date', direction: 'asc' }]} />
        <IntegratedSorting />
        <VirtualTable />
        <TableHeaderRow showSortingControls />
        <TableColumnVisibility />
        <SelectionState selection={selection} onSelectionChange={setSelection} />
        <IntegratedSelection />
        <TableSelection showSelectAll selectByRowClick />
        <TableFixedColumns rightColumns={rightColumns} />
        <Toolbar />
        <ColumnChooser />
      </ReactGrid>
    </Paper>
  )
}
