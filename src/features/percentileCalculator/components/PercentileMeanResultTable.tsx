import React from 'react'
import {
  Paper,
  TableContainer,
  Table,
  TableRow,
  TableCell,
  TableBody
} from '@material-ui/core'

import { MeanValues } from 'api/percentileAPI'
import { FWI_VALUES_DECIMAL_POINT } from 'utils/constants'

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
            <TableCell>{meanValues.ffmc.toFixed(FWI_VALUES_DECIMAL_POINT)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI mean value</TableCell>
            <TableCell>{meanValues.bui.toFixed(FWI_VALUES_DECIMAL_POINT)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI mean value</TableCell>
            <TableCell>{meanValues.isi.toFixed(FWI_VALUES_DECIMAL_POINT)}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}
