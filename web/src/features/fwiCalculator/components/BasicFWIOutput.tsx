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
  output: FWIOutput | null | undefined
}

const BasicFWIOutput = ({ isLoading, output }: BasicFWIOutputProps) => {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="Basic FWI Calculation Inputs">
        <TableBody>
          <TableRow>
            <TableCell>Today&apos;s Standard FFMC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output ? output.ffmc : ''}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard DMC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output ? output.dmc : ''}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard DC</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output ? output.dc : ''}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard ISI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output ? output.isi : ''}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard BUI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output ? output.bui : ''}</TableCell>
            )}
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard FWI</TableCell>
            {isLoading ? (
              <TableCell data-testid="loading-indicator-fwi">
                <Skeleton />
              </TableCell>
            ) : (
              <TableCell align="right">{output ? output.fwi : ''}</TableCell>
            )}
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIOutput)
