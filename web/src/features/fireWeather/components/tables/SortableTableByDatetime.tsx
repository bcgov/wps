import React, { useState } from 'react'
import * as _ from "lodash"
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
import Accordion from '@material-ui/core/Accordion'
import AccordionSummary from '@material-ui/core/AccordionSummary'
import AccordionDetails from '@material-ui/core/AccordionDetails'
import ExpandMoreIcon from '@material-ui/icons/ExpandMore'

import { getDatetimeComparator, Order } from 'utils/table'

const useStyles = makeStyles({
  display: {
    paddingBottom: 12,

    '& .MuiTableCell-sizeSmall': {
      padding: '6px 12px 6px 6px'
    }
  },
  paper: {
    width: '100%'
  },
  tableContainer: {
    maxHeight: 280
  },
  maxTemperature: {
    background: '#ffb3b3'
  },
  minTemperature: {
    background: '#84b8e7'
  },
  minRH: {
    background: '#f2994a'
  }
})

interface WeatherValue {
  datetime: string
  temperature?: number | null
  relative_humidity?: number | null
  dewpoint?: number | null
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

  if (!props.rows || props.rows.length === 0) {
    return null
  }

  const rowsSortedByDatetime = [...props.rows].sort(getDatetimeComparator(order))
  const toggleDatetimeOrder = () => {
    setOrder(order === 'asc' ? 'desc' : 'asc')
  }
  const minMaxValuesToHighlight = {
    'temperature': {
      'min_temperature': _.minBy(props.rows, 'temperature').temperature,
      'max_temperature': _.maxBy(props.rows, 'temperature').temperature,
    },
    'relative_humidity': _.minBy(props.rows, 'relative_humidity').relative_humidity,
    'precipitation': _.maxBy(props.rows, 'precipitation').precipitation,
    'wind_speed': _.maxBy(props.rows, 'wind_speed')
  }

  return (
    <div className={classes.display} data-testid={props.testId}>
      <Accordion defaultExpanded>
        <AccordionSummary
          data-testid={`${props.testId}-accordion`}
          expandIcon={<ExpandMoreIcon />}
        >
          <Typography component="div" variant="subtitle2">
            {props.title}
          </Typography>
        </AccordionSummary>

        <AccordionDetails>
          <Paper className={classes.paper} elevation={1}>
            <TableContainer className={classes.tableContainer}>
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
                        let className = undefined

                        if (typeof value === 'string' && column.formatDt) {
                          display = column.formatDt(value)
                        }
                        if (typeof value === 'number' && column.format) {
                          display = column.format(value)
                        }

                        if (column.id in minMaxValuesToHighlight) {
                          switch(column.id) {
                            case 'relative_humidity': {
                              if (display === column.format(minMaxValuesToHighlight['relative_humidity'])) {
                                className = classes.minRH
                              }
                              break
                            }
                            case 'temperature': {
                              if (display === column.format(minMaxValuesToHighlight['temperature']['min_temperature'])) {
                                className = classes.minTemperature
                              }
                              else if (display === column.format(minMaxValuesToHighlight['temperature']['max_temperature'])) {
                                className = classes.maxTemperature
                              }
                              break
                            }
                          }
                        }

                        return (
                          <TableCell key={column.id} align={column.align} className={className}>
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
        </AccordionDetails>
      </Accordion>
    </div>
  )
}

export default React.memo(SortableTableByDatetime)
