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
import { Station } from 'api/stationAPI'

const useStyles = makeStyles({
  root: {
    width: 400,
    marginTop: 15,
    marginRight: 15
  }
})

interface Props {
  station: Station
  stationResponse: StationSummaryResponse
}

export const PercentileResultTable = ({ station, stationResponse }: Props) => {
  const classes = useStyles()
  const { season, FFMC, BUI, ISI, year_range } = stationResponse
  const seasonRange = `${season.start_month}/${season.start_day} ~ ${season.end_month}/${season.end_day}`
  const yearRange = `${year_range.start} ~ ${year_range.end}`

  return (
    <TableContainer component={Paper} className={classes.root}>
      <Table aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Station Name (Code)</TableCell>
            <TableCell>
              {station.name} ({station.code})
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>FFMC</TableCell>
            <TableCell>{FFMC.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI</TableCell>
            <TableCell>{ISI.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI</TableCell>
            <TableCell>{BUI.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Season (mm/dd)</TableCell>
            <TableCell>{seasonRange}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Time Range</TableCell>
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
