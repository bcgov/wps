import {
  SelectionState,
  IntegratedSelection,
  IntegratedSorting,
  SortingState,
  EditingState,
  ChangeSet
} from '@devexpress/dx-react-grid'
import {
  ColumnChooser,
  Grid as ReactGrid,
  TableColumnVisibility,
  TableFixedColumns,
  TableHeaderRow,
  TableInlineCellEditing,
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
  const [rows, setRows] = useState(genRows)

  const commitChanges = (changes: ChangeSet) => {
    if (changes.added) {
      const startingAddedId = rows.length > 0 ? rows[rows.length - 1].id + 1 : 0
      const changedRows = [
        ...rows,
        ...changes.added.map((row, index) => ({
          id: startingAddedId + index,
          ...row
        }))
      ]
      setRows(changedRows)
    }
    if (changes.changed) {
      const changed = changes.changed
      const changedRows = rows.map(row =>
        changed[row.id] ? { ...row, ...changed[row.id] } : row
      )
      setRows(changedRows)
    }
  }

  return (
    <Paper>
      <ReactGrid rows={genRows} columns={columns}>
        <SortingState defaultSorting={[{ columnName: 'date', direction: 'asc' }]} />
        <IntegratedSorting />
        <EditingState onCommitChanges={commitChanges} />

        <VirtualTable />
        <TableHeaderRow showSortingControls />
        <TableColumnVisibility />
        <SelectionState selection={selection} onSelectionChange={setSelection} />
        <IntegratedSelection />
        <TableSelection showSelectAll />
        <TableFixedColumns rightColumns={rightColumns} />
        <TableInlineCellEditing />
        <Toolbar />
        <ColumnChooser />
      </ReactGrid>
    </Paper>
  )
}
