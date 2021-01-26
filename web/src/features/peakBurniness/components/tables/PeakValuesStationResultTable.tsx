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

  interface PeakValuesStationResultTableProps {
    stationResponse: StationPeakValues
  }

  export const PeakValuesStationResultTable: React.FunctionComponent<PeakValuesStationResultTableProps> = ({stationResponse}: PeakValuesStationResultTableProps) => {
    const { station, weeks } = stationResponse

    return (
      <div data-testid="peak-values-station-result-table">
        <Paper elevation={1}>
          <TableContainer >
              <Table stickyHeader size="small" aria-label="">
                <TableHead>
                  <TableRow>
                    <TableCell>Station Name</TableCell>
                    <TableCell>{station.name} ({station.code})</TableCell>
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