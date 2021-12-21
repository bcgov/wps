import {
  TableContainer,
  Paper,
  Table,
  TableRow,
  TableCell,
  TableBody,
  TableHead
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
        <TableHead>
          <TableRow>
            <TableCell align="center" colSpan={2}>
              Actual
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>FFMC</TableCell>
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
            <TableCell>DMC</TableCell>
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
            <TableCell>DC</TableCell>
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
            <TableCell>ISI</TableCell>
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
            <TableCell>BUI</TableCell>
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
            <TableCell>FWI</TableCell>
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
