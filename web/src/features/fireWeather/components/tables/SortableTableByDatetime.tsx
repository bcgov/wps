import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import TableHead from '@material-ui/core/TableHead'
import TableSortLabel from '@material-ui/core/TableSortLabel'
import Paper from '@material-ui/core/Paper'
import Typography from '@material-ui/core/Typography'
import KeyboardArrowUpIcon from '@material-ui/icons/KeyboardArrowUp'
import { Collapse, IconButton, Tooltip } from '@material-ui/core'

import { getDatetimeComparator, Order } from 'utils/table'

const useStyles = makeStyles({
  display: {
    paddingBottom: 12
  },
  paper: {
    width: '100%'
  },
  tableContainer: {
    maxHeight: 280
  },
  title: {
    paddingBottom: 4
  },
  clockwiseAnimation: {
    animation: '$rotateCW 250ms forwards'
  },
  counterClockwiseAnimation: {
    animation: '$rotateCCW 250ms forwards'
  },
  '@keyframes rotateCW': {
    from: { transform: 'rotate(0deg)' },
    to: { transform: 'rotate(180deg)' }
  },
  '@keyframes rotateCCW': {
    from: { transform: 'rotate(180deg)' },
    to: { transform: 'rotate(0deg)' }
  }
})

interface WeatherValue {
  datetime: string
  temperature?: number | null
  relative_humidity?: number | null
  wind_direction?: number | null
  wind_speed?: number | null
  precipitation?: number | null
  delta_precipitation?: number | null
  total_precipitation?: number | null
  ffmc?: number | null
  isi?: number | null
  fwi?: number | null
  model_run_datetime?: string | null
}

export interface Column {
  id: keyof WeatherValue
  label: string
  minWidth?: number
  maxWidth?: number
  align?: 'left' | 'right' | 'center'
  format?: (value: number) => string | number
  formatDt?: (dt: string) => string
}

interface Props<R> {
  testId: string
  title: string
  rows: R[] | undefined
  columns: Column[]
}

function SortableTableByDatetime<R extends WeatherValue>(props: Props<R>) {
  const classes = useStyles()
  const [order, setOrder] = useState<Order>('asc')
  const [open, setOpen] = useState(true)

  if (!props.rows || props.rows.length === 0) {
    return null
  }

  const rowsSortedByDatetime = [...props.rows].sort(getDatetimeComparator(order))
  const toggleDatetimeOrder = () => {
    setOrder(order === 'asc' ? 'desc' : 'asc')
  }

  const animate = () => {
    if (open) {
      return classes.counterClockwiseAnimation
    } else if (!open) {
      return classes.clockwiseAnimation
    }
  }

  interface TableHeaderProps {
    title: string
    testId?: string
  }

  const TableHeader = (tableHeaderProps: TableHeaderProps) => {
    const tableHeaderClasses = useStyles()
    return (
      <Paper
        data-testid={`${tableHeaderProps.testId}-header`}
        style={{ paddingLeft: '15px' }}
      >
        <Typography className={tableHeaderClasses.title} display="inline">
          {tableHeaderProps.title}
        </Typography>
        <Tooltip title={open ? 'Collapse table' : 'Expand table'}>
          <IconButton
            className={animate()}
            aria-label={open ? 'collapse table' : 'expand table'}
            size="small"
            onClick={() => setOpen(!open)}
            data-testid={`${tableHeaderProps.testId}-collapse`}
          >
            <KeyboardArrowUpIcon />
          </IconButton>
        </Tooltip>
      </Paper>
    )
  }

  return (
    <div className={classes.display} data-testid={props.testId}>
      <TableHeader title={props.title} testId={props.testId}></TableHeader>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
          <Collapse in={open} timeout={250} unmountOnExit>
            <Table stickyHeader size="small" aria-label="sortable wx table">
              <TableHead>
                <TableRow>
                  {props.columns.map(column => {
                    const canSort = column.id === 'datetime'

                    return (
                      <TableCell
                        key={column.id}
                        align={column.align}
                        style={{ minWidth: column.minWidth, maxWidth: column.maxWidth }}
                        sortDirection={canSort ? order : false}
                      >
                        {canSort ? (
                          <TableSortLabel
                            active={canSort}
                            direction={order}
                            onClick={toggleDatetimeOrder}
                          >
                            {column.label}
                          </TableSortLabel>
                        ) : (
                          column.label
                        )}
                      </TableCell>
                    )
                  })}
                </TableRow>
              </TableHead>

              <TableBody>
                {rowsSortedByDatetime.map((row, idx) => (
                  <TableRow key={idx} hover tabIndex={-1}>
                    {props.columns.map(column => {
                      const value = row[column.id]
                      let display = null

                      if (typeof value === 'string' && column.formatDt) {
                        display = column.formatDt(value)
                      }
                      if (typeof value === 'number' && column.format) {
                        display = column.format(value)
                      }

                      return (
                        <TableCell key={column.id} align={column.align}>
                          {display}
                        </TableCell>
                      )
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Collapse>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(SortableTableByDatetime)
