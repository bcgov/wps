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

interface Props {
  stationResponse: StationSummaryResponse
}

export const PercentileStationResultTable = ({ stationResponse }: Props) => {
  const { season, ffmc, bui, isi, years, station } = stationResponse
  const seasonRange = `${season.start_month}/${season.start_day} ~ ${season.end_month}/${season.end_day}`
  const yearRange = years.join(', ')

  return (
    <TableContainer component={Paper}>
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
            <TableCell>{ffmc.toFixed(FWI_VALUES_DECIMAL)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI</TableCell>
            <TableCell>{bui.toFixed(FWI_VALUES_DECIMAL)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI</TableCell>
            <TableCell>{isi.toFixed(FWI_VALUES_DECIMAL)}</TableCell>
          </TableRow>

          <TableRow>
            <TableCell>Season (mm/dd)</TableCell>
            <TableCell>{seasonRange}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Years</TableCell>
            <TableCell>{yearRange}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Percentile (%)</TableCell>
            <TableCell>90</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}
