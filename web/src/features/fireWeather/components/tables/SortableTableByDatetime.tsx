import React, { useState } from 'react'
import * as _ from 'lodash'
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
  },
  maxPrecipitation: {
    fontWeight: 'bold',
    borderColor: 'black',
    borderStyle: 'solid',
    borderWidth: '2px'
  },
  maxWindSpeed: {
    fontWeight: 'bold',
    borderColor: 'black',
    borderStyle: 'solid',
    borderTopWidth: '2px',
    borderBottomWidth: '2px',
    borderRightWidth: '2px',
    borderLeftWidth: '0px'
  },
  directionOfMaxWindSpeed: {
    fontWeight: 'bold',
    borderColor: 'black',
    borderStyle: 'solid',
    borderTopWidth: '2px',
    borderBottomWidth: '2px',
    borderLeftWidth: '2px',
    borderRightWidth: '0px'
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

interface MinMaxValues {
  relative_humidity: number | null
  precipitation: number | null
  wind_speed: number | null
  temperature: {
    min: number | null
    max: number | null
  }
}

interface RowIdsOfMinMaxValues {
  relative_humidity: number[]
  precipitation: number[]
  wind: number[]
  max_temp: number[]
  min_temp: number[]
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

  const minMaxValuesToHighlight: MinMaxValues = {
    relative_humidity:
      _.minBy(props.rows, 'relative_humidity')?.relative_humidity ?? null,
    precipitation: _.maxBy(props.rows, 'precipitation')?.precipitation ?? null,
    wind_speed: _.maxBy(props.rows, 'wind_speed')?.wind_speed ?? null,
    temperature: {
      min: _.minBy(props.rows, 'temperature')?.temperature ?? null,
      max: _.maxBy(props.rows, 'temperature')?.temperature ?? null
    }
  }

  const rowIds: RowIdsOfMinMaxValues = {
    relative_humidity: [],
    precipitation: [],
    wind: [],
    max_temp: [],
    min_temp: []
  }

  rowsSortedByDatetime.map((row, idx) => {
    console.log(row, idx)
    if (row.relative_humidity === minMaxValuesToHighlight.relative_humidity) {
      rowIds['relative_humidity'].push(idx)
    }
    if (row.precipitation === minMaxValuesToHighlight.precipitation) {
      rowIds['precipitation'].push(idx)
    }
    if (row.temperature === minMaxValuesToHighlight.temperature.max) {
      rowIds['max_temp'].push(idx)
    }
    if (row.temperature === minMaxValuesToHighlight.temperature.min) {
      rowIds['min_temp'].push(idx)
    }
    if (row.wind_speed === minMaxValuesToHighlight.wind_speed) {
      rowIds['wind'].push(idx)
    }
  })

  console.log(minMaxValuesToHighlight)
  console.log(rowIds)

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

                        switch (column.id) {
                          case 'relative_humidity': {
                            if (rowIds['relative_humidity'].includes(idx)) {
                              className = classes.minRH
                            }
                            break
                          }
                          case 'temperature': {
                            if (rowIds['min_temp'].includes(idx)) {
                              className = classes.minTemperature
                            } else if (rowIds['max_temp'].includes(idx)) {
                              className = classes.maxTemperature
                            }
                            break
                          }
                          case 'precipitation': {
                            if (rowIds['precipitation'].includes(idx)) {
                              className = classes.maxPrecipitation
                            }
                            break
                          }
                          case 'wind_speed': {
                            if (rowIds['wind'].includes(idx)) {
                              className = classes.maxWindSpeed
                            }
                            break
                          }
                          case 'wind_direction': {
                            if (rowIds['wind'].includes(idx)) {
                              className = classes.directionOfMaxWindSpeed
                            }
                            break
                          }
                        }

                        return (
                          <TableCell
                            key={column.id}
                            align={column.align}
                            className={className}
                          >
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
