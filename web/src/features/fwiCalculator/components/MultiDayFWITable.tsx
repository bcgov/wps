import { SelectionState, IntegratedSelection } from '@devexpress/dx-react-grid'
import {
  Grid as ReactGrid,
  Table,
  TableFixedColumns,
  TableHeaderRow,
  TableSelection
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

  const [leftColumns] = useState([
    TableSelection.COLUMN_TYPE,
    'id',
    TableSelection.COLUMN_TYPE,
    'date'
  ])

  const [selection, setSelection] = useState<(string | number)[]>([])

  const dates = getDaysBetween(startDate, endDate)
  const genRows = generateDefaultRowsFromDates(dates)

  return (
    <Paper>
      <ReactGrid rows={genRows} columns={columns}>
        <Table />
        <TableHeaderRow />
        <SelectionState selection={selection} onSelectionChange={setSelection} />
        <IntegratedSelection />
        <TableSelection showSelectAll />
        <TableFixedColumns leftColumns={leftColumns} />
      </ReactGrid>
    </Paper>
  )
}
