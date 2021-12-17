import {
  TableContainer,
  Paper,
  Table,
  TableRow,
  TableCell,
  TableBody
} from '@material-ui/core'
import { FWIOutput } from 'api/fwiAPI'
import React from 'react'

export interface BasicFWIOutputProps {
  output: FWIOutput | null | undefined
}

const BasicFWIOutput = ({ output }: BasicFWIOutputProps) => {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="Basic FWI Calculation Inputs">
        <TableBody>
          <TableRow>
            <TableCell>Today&apos;s Standard FFMC</TableCell>
            <TableCell>{output ? output.ffmc : ''}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard DMC</TableCell>
            <TableCell>{output ? output.dmc : ''}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard DC</TableCell>
            <TableCell>{output ? output.dc : ''}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard ISI</TableCell>
            <TableCell>{output ? output.isi : ''}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard BUI</TableCell>
            <TableCell>{output ? output.bui : ''}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard FWI</TableCell>
            <TableCell>{output ? output.fwi : ''}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIOutput)
