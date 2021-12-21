import { SelectionState, IntegratedSelection } from '@devexpress/dx-react-grid'
import {
  Grid as ReactGrid,
  Table,
  TableFixedColumns,
  TableHeaderRow,
  TableSelection
} from '@devexpress/dx-react-grid-material-ui'
import { Paper } from '@material-ui/core'
import React, { useState } from 'react'

export const MultiDayFWITable = (): JSX.Element => {
  const [columns] = useState([
    { name: 'date', title: 'Date' },
    { name: 'status', title: 'Status' },
    { name: 'temp', title: 'Temperature' },
    { name: 'rh', title: 'Relative Humidity' }
  ])

  const [rows] = useState([
    { id: 0, date: '01/02/2021', status: 'FORECAST', temp: '1', rh: '1' },
    { id: 1, date: '02/04/2020', status: 'ACTUAL', temp: '1', rh: '1' }
  ])

  const [leftColumns] = useState([
    TableSelection.COLUMN_TYPE,
    'id',
    TableSelection.COLUMN_TYPE,
    'date'
  ])

  const [selection, setSelection] = useState<(string | number)[]>([])

  const [tableColumnExtensions] = useState([
    { columnName: 'date' },
    { columnName: 'status' },
    { columnName: 'temperature' },
    { columnName: 'RH' }
  ])

  return (
    <Paper>
      <ReactGrid rows={rows} columns={columns}>
        <Table columnExtensions={tableColumnExtensions} />
        <TableHeaderRow />
        <SelectionState selection={selection} onSelectionChange={setSelection} />
        <IntegratedSelection />
        <TableSelection showSelectAll />
        <TableFixedColumns leftColumns={leftColumns} />
      </ReactGrid>
    </Paper>
  )
}
