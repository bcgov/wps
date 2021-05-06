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
import { TEMPERATURE_VALUES_DECIMAL, RH_VALUES_DECIMAL, WIND_SPEED_VALUES_DECIMAL, FFMC_VALUES_DECIMAL, FWI_VALUES_DECIMAL } from 'utils/constants'

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
    label: 'Max Temp (°C)',
    align: 'right',
    format: (value: number): string => value.toFixed(TEMPERATURE_VALUES_DECIMAL)
  },
  {
    id: 'hour_max_temp',
    label: 'Hour of Max Temp',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'min_rh',
    label: 'Min RH (%)',
    align: 'right',
    format: (value: number): string => value.toFixed(RH_VALUES_DECIMAL)
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
    format: (value: number): string => value.toFixed(WIND_SPEED_VALUES_DECIMAL)
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
    format: (value: number): string => value.toFixed(FFMC_VALUES_DECIMAL)
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
    format: (value: number): string => value.toFixed(FWI_VALUES_DECIMAL)
  },
  {
    id: 'hour_max_fwi',
    label: 'Hour of Max FWI',
    align: 'right',
    format: (value: number): string => value.toString()
  }
]

const useStyles = makeStyles(theme => ({
  display: {
    paddingBottom: 12
  },
  paper: {
    width: '100%'
  },
  tableContainer: {
    maxHeight: 500,
    paddingBottom: 10,
    marginTop: 15,
    marginBottom: 10
  },
  title: {
    paddingBottom: 4
  },
  stationTitle: {
    padding: 5,
    backgroundColor: theme.palette.primary.light,
    color: '#ffffff'
  }
}))

interface PeakValuesStationResultTableProps {
  stationResponse: StationPeakValues
}

export const PeakValuesStationResultTable: React.FunctionComponent<PeakValuesStationResultTableProps> = ({
  stationResponse
}: PeakValuesStationResultTableProps) => {
  const classes = useStyles()
  const { code, weeks } = stationResponse

  return (
    <div data-testid="peak-values-station-result-table">
      <Paper className={classes.paper} elevation={1}>
        <Paper className={classes.stationTitle} elevation={2}>
          <Typography>Station {code}</Typography>
        </Paper>
        <TableContainer className={classes.tableContainer}>
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
              {weeks.map((row: PeakWeekValues, idx: number) => (
                <TableRow key={idx} hover tabIndex={-1}>
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
