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
import { makeStyles } from '@material-ui/core/styles'
import { StationSummaryResponse } from 'api/percentileAPI'

const useStyles = makeStyles({
  root: {
    width: 400,
    marginTop: 15,
    marginRight: 15
  }
})

interface Props {
  stationCode: string
  stationResponse: StationSummaryResponse
}

export const PercentileStationResultTable = ({
  stationCode,
  stationResponse
}: Props) => {
  const classes = useStyles()
  const { season, FFMC, BUI, ISI, years, station_name } = stationResponse
  const seasonRange = `${season.start_month}/${season.start_day} ~ ${season.end_month}/${season.end_day}`
  const yearRange = years.join(', ')

  return (
    <TableContainer component={Paper} className={classes.root}>
      <Table aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Station Name</TableCell>
            <TableCell>
              {station_name} ({stationCode})
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>FFMC</TableCell>
            <TableCell>{FFMC.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI</TableCell>
            <TableCell>{BUI.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI</TableCell>
            <TableCell>{ISI.toFixed(1)}</TableCell>
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
