import React from 'react'
import { MeanValues } from 'api/percentileAPI'
import {
  Paper,
  TableContainer,
  Table,
  TableRow,
  TableCell,
  TableBody
} from '@material-ui/core'

interface Props {
  meanValues: MeanValues
}

export const PercentileMeanResultTable = ({ meanValues }: Props) => {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="simple table">
        <TableBody>
          <TableRow>
            <TableCell>FFMC mean value</TableCell>
            <TableCell>{meanValues.FFMC.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI mean value</TableCell>
            <TableCell>{meanValues.BUI.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI mean value</TableCell>
            <TableCell>{meanValues.ISI.toFixed(1)}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}
