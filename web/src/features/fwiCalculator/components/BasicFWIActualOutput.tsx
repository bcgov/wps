import {
  TableContainer,
  Paper,
  Table,
  TableRow,
  TableCell,
  TableBody
} from '@material-ui/core'
import { Skeleton } from '@material-ui/lab'
import { FWIOutput } from 'api/fwiAPI'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface BasicFWIOutputProps {
  isLoading: boolean
  output: FWIOutput
}

const BasicFWIActualOutput = ({ isLoading, output }: BasicFWIOutputProps) => {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="Basic FWI Calculation Inputs">
        <TableBody>
          <TableRow>
            <TableCell>Actual FFMC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.actual?.ffmc?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Actual DMC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.actual?.dmc?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Actual DC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.actual?.dc?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Actual ISI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.actual?.isi?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Actual BUI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.actual?.bui?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Actual FWI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.actual?.fwi?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIActualOutput)
