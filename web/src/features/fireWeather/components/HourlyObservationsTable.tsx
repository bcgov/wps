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

import { HOURLY_VALUES_DECIMAL } from 'utils/constants'
import { ObservedValue } from 'api/observationAPI'
import { formatDateInPDT } from 'utils/date'
import { getDatetimeComparator, Order } from 'utils/table'

const useStyles = makeStyles({
  display: {
    paddingBottom: 8
  },
  paper: {
    width: '100%'
  },
  tableContainer: {
    maxHeight: 300
  },
  title: {
    paddingBottom: 4
  }
})

interface Column {
  id: keyof ObservedValue
  label: string
  minWidth?: number
  maxWidth?: number
  align?: 'left' | 'right' | 'center'
  format?: (value: number) => string | number
}

const columns: Column[] = [
  { id: 'datetime', label: 'Date (PDT)', minWidth: 120, align: 'left' },
  {
    id: 'temperature',
    label: 'Temp (°C)',
    align: 'right',
    format: (value: number) => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'relative_humidity',
    label: 'RH (%)',
    align: 'right',
    format: (value: number) => Math.round(value)
  },
  {
    id: 'wind_direction',
    label: 'Wind Dir',
    align: 'right',
    format: (value: number) => Math.round(value)
  },
  {
    id: 'wind_speed',
    label: 'Wind Spd (km/h)',
    minWidth: 70,
    maxWidth: 100,
    align: 'right',
    format: (value: number) => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'precipitation',
    label: 'Precip (mm/cm)',
    minWidth: 70,
    maxWidth: 100,
    align: 'right',
    format: (value: number) => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'ffmc',
    label: 'FFMC',
    align: 'right',
    format: (value: number) => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'isi',
    label: 'ISI',
    align: 'right',
    format: (value: number) => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'fwi',
    label: 'FWI',
    align: 'right',
    format: (value: number) => value.toFixed(HOURLY_VALUES_DECIMAL)
  }
]

interface Props {
  title: string
  rows: ObservedValue[] | undefined
}

const HourlyObservationsTable = (props: Props) => {
  const classes = useStyles()
  const [order, setOrder] = useState<Order>('asc')

  if (!props.rows) {
    return null
  }

  const rowsSortedByDatetime = [...props.rows].sort(getDatetimeComparator(order))
  const toggleDatetimeOrder = () => {
    setOrder(order === 'asc' ? 'desc' : 'asc')
  }

  return (
    <div className={classes.display} data-testid="hourly-observations-table">
      <Typography className={classes.title} component="div" variant="subtitle2">
        {props.title}
      </Typography>

      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
          <Table stickyHeader size="small" aria-label="observation table">
            <TableHead>
              <TableRow>
                {columns.map(column => {
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
                  {columns.map(column => {
                    const value = row[column.id]
                    let display = null

                    if (typeof value === 'string' && column.id === 'datetime') {
                      display = formatDateInPDT(value)
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
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(HourlyObservationsTable)
