import React, { useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableRow from '@mui/material/TableRow'
import TableHead from '@mui/material/TableHead'
import TableSortLabel from '@mui/material/TableSortLabel'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Accordion from '@mui/material/Accordion'
import AccordionSummary from '@mui/material/AccordionSummary'
import AccordionDetails from '@mui/material/AccordionDetails'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

import {
  getDatetimeComparator,
  getMinMaxValueCalculator,
  Order,
  MinMaxValues,
  RowIdsOfMinMaxValues,
  getMinMaxValuesRowIds,
  getCellClassNameAndTestId
} from 'utils/table'

const useStyles = makeStyles({
  display: {
    paddingBottom: 12,

    '& .MuiTableCell-sizeSmall': {
      padding: '3px 6px 3px 2px'
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
    borderColor: 'rgba(0, 0, 0, 0.87)',
    borderStyle: 'solid',
    borderWidth: '1px'
  },
  maxWindSpeed: {
    fontWeight: 'bold',
    borderColor: 'rgba(0, 0, 0, 0.87)',
    borderStyle: 'solid',
    borderTopWidth: '1px',
    borderBottomWidth: '1px',
    borderRightWidth: '1px',
    borderLeftWidth: '0px'
  },
  directionOfMaxWindSpeed: {
    fontWeight: 'bold',
    borderColor: 'rgba(0, 0, 0, 0.87)',
    borderStyle: 'solid',
    borderTopWidth: '1px',
    borderBottomWidth: '1px',
    borderLeftWidth: '1px',
    borderRightWidth: '0px'
  }
})

export interface WeatherValue {
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
  format?: (value: number) => string | number | undefined
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
  const [order, setOrder] = useState<Order>('desc')

  if (!props.rows || props.rows.length === 0) {
    return null
  }

  const rowsSortedByDatetime = [...props.rows].sort(getDatetimeComparator(order))
  const toggleDatetimeOrder = () => {
    setOrder(order === 'asc' ? 'desc' : 'asc')
  }

  const minMaxValuesToHighlight: MinMaxValues = getMinMaxValueCalculator(rowsSortedByDatetime)
  const rowIds: RowIdsOfMinMaxValues = getMinMaxValuesRowIds(rowsSortedByDatetime, minMaxValuesToHighlight)

  return (
    <div className={classes.display} data-testid={props.testId}>
      <Accordion defaultExpanded>
        <AccordionSummary data-testid={`${props.testId}-accordion`} expandIcon={<ExpandMoreIcon />}>
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
                            <TableSortLabel active={canSort} direction={order} onClick={toggleDatetimeOrder}>
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
                        const { className, testId } = getCellClassNameAndTestId(column, rowIds, idx, classes)

                        if (typeof value === 'string' && column.formatDt) {
                          display = column.formatDt(value)
                        }
                        if (typeof value === 'number' && column.format) {
                          display = column.format(value)
                        }

                        return (
                          <TableCell key={column.id} align={column.align} className={className} data-testid={testId}>
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
