import {
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
import { Container } from 'components'
import { CircularProgress, Paper, makeStyles } from '@material-ui/core'
import { selectMultiFWIOutputs, selectMultiFWIOutputsLoading } from 'app/rootReducer'
import {
  defaultColumns,
  disabledColumns,
  generateDefaultRowsFromDates,
  MultiDayRow,
  output2Rows
} from 'features/fwiCalculator/components/dataModel'
import FireIndexGraph from 'features/fwiCalculator/components/FireIndexGraph'
import { fetchMultiFWICalculation } from 'features/fwiCalculator/slices/multiFWISlice'
import { DateTime, Interval } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { getDaysBetween } from 'utils/date'
export interface Option {
  name: string
  code: number
}

export interface MultiDayFWITableProps {
  selectedStation: Option | null
  startDate: string
  endDate: string
}

const useStyles = makeStyles(() => ({
  container: {
    display: 'flex',
    justifyContent: 'center'
  }
}))

export const MultiDayFWITable = ({
  selectedStation,
  startDate,
  endDate
}: MultiDayFWITableProps): JSX.Element => {
  const classes = useStyles()
  const dispatch = useDispatch()
  const { multiFWIOutputs } = useSelector(selectMultiFWIOutputs)
  const isLoading = useSelector(selectMultiFWIOutputsLoading)
  const [columns] = useState(defaultColumns)

  const rightColumns = [
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
  ]

  const leftColumns = [TableSelection.COLUMN_TYPE, 'date']

  const [rows, setRows] = useState<MultiDayRow[]>([])

  useEffect(() => {
    if (
      Interval.fromDateTimes(DateTime.fromISO(startDate), DateTime.fromISO(endDate))
        .isValid
    ) {
      const dates = getDaysBetween(startDate, endDate)

      const newRows = generateDefaultRowsFromDates(dates)
      setRows(newRows)
      dispatch(fetchMultiFWICalculation(selectedStation, newRows))
    }
  }, [startDate, endDate, selectedStation]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const newRows = output2Rows(multiFWIOutputs)
    setRows(newRows)
  }, [multiFWIOutputs]) // eslint-disable-line react-hooks/exhaustive-deps

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
      dispatch(fetchMultiFWICalculation(selectedStation, changedRows))
    }
  }

  return (
    <React.Fragment>
      <Paper>
        {isLoading ? (
          <Container className={classes.container}>
            <CircularProgress />
          </Container>
        ) : (
          <React.Fragment>
            <ReactGrid rows={rows} columns={columns}>
              <SortingState defaultSorting={[{ columnName: 'date', direction: 'asc' }]} />
              <IntegratedSorting />
              <EditingState
                onCommitChanges={commitChanges}
                columnExtensions={isLoading ? disabledColumns : undefined}
              />
              <VirtualTable />
              <TableHeaderRow showSortingControls />
              <TableColumnVisibility />
              <TableFixedColumns leftColumns={leftColumns} rightColumns={rightColumns} />
              <TableInlineCellEditing />
              <Toolbar />
              <ColumnChooser />
            </ReactGrid>
            <FireIndexGraph rowData={rows} />
          </React.Fragment>
        )}
      </Paper>
    </React.Fragment>
  )
}
