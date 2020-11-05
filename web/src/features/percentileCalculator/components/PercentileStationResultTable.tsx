import React from 'react'
import {
  TableContainer,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody
} from '@material-ui/core'

import { StationSummaryResponse } from 'api/percentileAPI'
import { FWI_VALUES_DECIMAL } from 'utils/constants'
import { formatMonthAndDay } from 'utils/date'
import { NOT_AVAILABLE } from 'utils/strings'

interface Props {
  stationResponse: StationSummaryResponse
}

export const PercentileStationResultTable: React.FunctionComponent<Props> = ({
  stationResponse
}: Props) => {
  const { ffmc, bui, isi, years, station } = stationResponse
  const { start_month, start_day, end_month, end_day } = station.core_season
  const seasonRange = `${formatMonthAndDay(start_month, start_day)}\
   ~ ${formatMonthAndDay(end_month, end_day)}`
  const yearRange = years.join(', ')

  return (
    <TableContainer component={Paper} data-testid="percentile-station-result-table">
      <Table aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Station Name</TableCell>
            <TableCell>
              {station.name} ({station.code})
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>FFMC</TableCell>
            <TableCell data-testid="percentile-station-result-FFMC">
              {ffmc ? ffmc.toFixed(FWI_VALUES_DECIMAL) : NOT_AVAILABLE}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI</TableCell>
            <TableCell data-testid="percentile-station-result-BUI">
              {bui ? bui.toFixed(FWI_VALUES_DECIMAL) : NOT_AVAILABLE}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI</TableCell>
            <TableCell data-testid="percentile-station-result-ISI">
              {isi ? isi.toFixed(FWI_VALUES_DECIMAL) : NOT_AVAILABLE}
            </TableCell>
          </TableRow>

          <TableRow>
            <TableCell>Eco-division</TableCell>
            <TableCell>{station.ecodivision_name}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Core Fire Season</TableCell>
            <TableCell>{seasonRange}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Years</TableCell>
            <TableCell>{yearRange}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Percentile</TableCell>
            <TableCell>90th</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}
