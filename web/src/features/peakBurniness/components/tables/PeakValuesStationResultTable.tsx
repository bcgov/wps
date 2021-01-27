import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import TableHead from '@material-ui/core/TableHead'
import Paper from '@material-ui/core/Paper'
import Typography from '@material-ui/core/Typography'
import { PeakWeekValues, StationPeakValues } from 'api/peakBurninessAPI'
import { MODEL_VALUE_DECIMAL } from 'utils/constants'

interface Column {
  id: keyof PeakWeekValues
  label: string
  minWidth?: number
  maxWidth?: number
  align?: 'left' | 'right' | 'center'
  format?: (value: number) => string | number
  formatStr?: (value: string) => string
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

interface PeakValuesStationResultTableProps {
  stationResponse: StationPeakValues
}

export const PeakValuesStationResultTable: React.FunctionComponent<PeakValuesStationResultTableProps> = ({
  stationResponse
}: PeakValuesStationResultTableProps) => {
  const { code, weeks } = stationResponse

  console.log(code, weeks)

  return (
    <div data-testid="peak-values-station-result-table">
      <Paper elevation={1}>
        <Typography>Station {code}</Typography>
        <TableContainer>
          <Table stickyHeader size="small" aria-label="">
            <TableHead>
              <TableRow>
                {columns.map(column => {
                  return (
                    <TableCell key={column.id} align={column.align}>
                      {column.label}
                    </TableCell>
                  )
                })}
              </TableRow>
            </TableHead>

            <TableBody>
              {weeks.map((row: PeakWeekValues) => (
                <TableRow hover tabIndex={-1}>
                  <TableCell>{row.week}</TableCell>
                  <TableCell>{row.max_temp}</TableCell>
                  <TableCell>{row.hour_max_temp}</TableCell>
                  <TableCell>{row.min_rh}</TableCell>
                  <TableCell>{row.hour_min_rh}</TableCell>
                  <TableCell>{row.max_wind_speed}</TableCell>
                  <TableCell>{row.hour_max_wind_speed}</TableCell>
                  <TableCell>{row.max_ffmc}</TableCell>
                  <TableCell>{row.hour_max_ffmc}</TableCell>
                  <TableCell>{row.max_fwi}</TableCell>
                  <TableCell>{row.hour_max_fwi}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(PeakValuesStationResultTable)
