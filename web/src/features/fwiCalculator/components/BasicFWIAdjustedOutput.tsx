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

const BasicFWIAdjustedOutput = ({ isLoading, output }: BasicFWIOutputProps) => {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="Basic FWI Calculation Inputs">
        <TableBody>
          <TableRow>
            <TableCell>Adjusted FFMC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.adjusted?.ffmc?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Adjusted DMC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.adjusted?.dmc?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Adjusted DC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.adjusted?.dc?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Adjusted ISI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.adjusted?.isi?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Adjusted BUI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.adjusted?.bui?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Adjusted FWI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">
                {output?.adjusted?.fwi?.toFixed(DECIMAL_PLACES)}
              </TableCell>
            )}
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIAdjustedOutput)
