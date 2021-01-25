import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import TableHead from '@material-ui/core/TableHead'
import Paper from '@material-ui/core/Paper'
import Typography from '@material-ui/core/Typography'

import { MODEL_VALUE_DECIMAL } from 'utils/constants'

interface PeakWeatherValue {
  week: string
  max_temp?: number | null
  min_rh?: number | null
  max_wind_speed?: number | null
  max_ffmc?: number | null
  max_fwi?: number | null
  hour_max_temp?: number | null
  hour_min_rh?: number | null
  hour_max_wind_speed?: number | null
  hour_max_ffmc?: number | null
  hour_max_fwi?: number | null
}

interface Column {
  id: keyof PeakWeatherValue
  label: string
  minWidth?: number
  maxWidth?: number
  align?: 'left' | 'right' | 'center'
  format?: (value: number) => string | number
  formatStr?: (value: string) => string
}

export interface Props<R> {
  testId: string
  title: string
  rows: R[] | undefined
  columns: Column[]
}

export const columns: Column[] = [
  {
    id: 'week',
    label: 'Week',
    align: 'left',
    formatStr: (value: string): string => value
  },
  {
    id: 'max_temp',
    label: 'Max Hourly Temp (°C)',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_max_temp',
    label: 'Hour of Max Temp',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'min_rh',
    label: 'Min Hourly RH (%)',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_min_rh',
    label: 'Hour of Min RH',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'max_wind_speed',
    label: 'Max Wind Speed (km/h)',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_max_wind_speed',
    label: 'Hour of Max Wind Speed',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'max_ffmc',
    label: 'Max FFMC',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_max_ffmc',
    label: 'Hour of Max FFMC',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'max_fwi',
    label: 'Max FWI',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_max_fwi',
    label: 'Hour of Max FWI',
    align: 'right',
    format: (value: number): string => value.toString()
  }
]

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
  }
})

function PeakValuesTable<R extends PeakWeatherValue>(props: Props<R>) {
  const classes = useStyles()

  if (!props.rows || props.rows.length === 0) {
    return null
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
      </Paper>
    )
  }

  return (
    <div className={classes.display} data-testid={props.testId}>
      <TableHeader title={props.title} testId={props.testId}></TableHeader>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
            <Table stickyHeader size="small" aria-label="">
              <TableHead>
                <TableRow>
                  {props.columns.map(column => {
                    return (
                      <TableCell key={column.id}>
                        {column.label}
                      </TableCell>
                    )
                  })}
                </TableRow>
              </TableHead>

              <TableBody>
                {props.rows.map((row: { [x: string]: any }, idx: string | number | null | undefined) => (
                  <TableRow key={idx} hover tabIndex={-1}>
                    {props.columns.map((column) => {
                      const value = row[column.id]
                      let display = null

                      if (typeof value === 'number' && column.format) {
                        display = column.format(value)
                      }

                      if (typeof value === 'string' && column.formatStr) {
                        display = column.formatStr(value)
                      }

                      return (
                        <TableCell key={column.id}>
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

export default React.memo(PeakValuesTable)

