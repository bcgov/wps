import { IntegratedSorting, SortingState, EditingState, ChangeSet } from '@devexpress/dx-react-grid'
import {
  ColumnChooser,
  Grid as ReactGrid,
  Table,
  TableColumnVisibility,
  TableFixedColumns,
  TableHeaderRow,
  TableInlineCellEditing,
  TableSelection,
  Toolbar
} from '@devexpress/dx-react-grid-material-ui'
import { Paper, IconButton, LinearProgress } from '@mui/material'
import { Add, Refresh } from '@mui/icons-material'
import { selectMultiFWIOutputs, selectMultiFWIOutputsLoading } from 'app/rootReducer'
import {
  defaultColumns,
  allDisabledColumns,
  generateDefaultRowsFromDates,
  MultiDayRow,
  output2Rows,
  updateRows,
  outputColumns
} from 'features/fwiCalculator/components/dataModel'
import FireIndexGraph from 'features/fwiCalculator/components/FireIndexGraph'
import { fetchMultiFWICalculation } from 'features/fwiCalculator/slices/multiFWISlice'
import { DateTime, Interval } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { getDaysBetween } from 'utils/date'
import { Template, TemplatePlaceholder } from '@devexpress/dx-react-core'
import { last, pick } from 'lodash'
import { MultiFWITableCell } from 'features/fwiCalculator/components/MultiFWITableCell'
import { AppDispatch } from 'app/store'
export interface Option {
  name: string
  code: number
}

export interface MultiDayFWITableProps {
  selectedStation: Option | null
  startDate: string
  endDate: string
}

export const MultiDayFWITable = ({ selectedStation, startDate, endDate }: MultiDayFWITableProps): JSX.Element => {
  const dispatch: AppDispatch = useDispatch()
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

  const loadFromRange = () => {
    if (Interval.fromDateTimes(DateTime.fromISO(startDate), DateTime.fromISO(endDate)).isValid) {
      const dates = getDaysBetween(startDate, endDate)
      const newRows = generateDefaultRowsFromDates(dates)
      setRows(newRows)
      dispatch(fetchMultiFWICalculation(selectedStation, newRows))
    }
  }

  useEffect(() => {
    loadFromRange()
  }, [startDate, endDate, selectedStation]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const newRows = output2Rows(multiFWIOutputs)
    const updatedRows = updateRows(rows, newRows)
    setRows(updatedRows)
  }, [multiFWIOutputs]) // eslint-disable-line react-hooks/exhaustive-deps

  const addRow = () => {
    commitChanges({ added: [{ ...pick(last(rows), ['date', 'isoDate']) }] })
  }

  const resetFromRange = () => {
    loadFromRange()
  }

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
      const allRowsWithChanges = rows.map(row => {
        if (changed[row.id]) {
          Object.keys(changed[row.id]).forEach(key => {
            changed[row.id][key] = Number(changed[row.id][key])
          })
        }

        return changed[row.id] ? { ...row, ...changed[row.id] } : row
      })
      setRows(allRowsWithChanges)
      const changedRows = allRowsWithChanges.filter(row => changed[row.id] !== undefined)
      dispatch(fetchMultiFWICalculation(selectedStation, changedRows))
    }
  }

  const disabledColumns = isLoading ? allDisabledColumns : outputColumns

  return (
    <React.Fragment>
      <Paper>
        <ReactGrid rows={rows} columns={columns}>
          {isLoading && <LinearProgress />}
          <SortingState defaultSorting={[{ columnName: 'date', direction: 'asc' }]} />
          <IntegratedSorting />
          <EditingState onCommitChanges={commitChanges} columnExtensions={disabledColumns} />
          <Table cellComponent={MultiFWITableCell} />
          <TableHeaderRow showSortingControls />
          <TableColumnVisibility />
          <TableFixedColumns leftColumns={leftColumns} rightColumns={rightColumns} />
          <TableInlineCellEditing />
          <Toolbar />
          <Template name="toolbarContent">
            <TemplatePlaceholder />
            <IconButton onClick={resetFromRange}>
              <Refresh />
            </IconButton>
            <IconButton onClick={addRow}>
              <Add />
            </IconButton>
          </Template>
          <ColumnChooser />
        </ReactGrid>
        <FireIndexGraph rowData={rows} />
      </Paper>
    </React.Fragment>
  )
}
