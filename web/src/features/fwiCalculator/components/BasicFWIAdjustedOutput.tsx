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
            <TableCell>Today&apos;s Adjusted FFMC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output.adjusted?.ffmc}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Adjusted DMC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output.adjusted?.dmc}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Adjusted DC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output.adjusted?.dc}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Adjusted ISI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output.adjusted?.isi}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Adjusted BUI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output.adjusted?.bui}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Adjusted FWI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output.adjusted?.fwi}</TableCell>
            )}
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIAdjustedOutput)
