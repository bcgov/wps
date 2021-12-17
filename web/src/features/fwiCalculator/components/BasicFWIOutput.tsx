import {
  TableContainer,
  Paper,
  Table,
  TableRow,
  TableCell,
  TableBody
} from '@material-ui/core'
import React from 'react'

const BasicFWIOutput = () => {
  return (
    <TableContainer component={Paper}>
      {/** Output table */}
      <Table aria-label="Basic FWI Calculation Inputs">
        <TableBody>
          <TableRow>
            <TableCell>Today&apos;s Standard FFMC</TableCell>
            <TableCell>100</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard DMC</TableCell>
            <TableCell>5</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard DC</TableCell>
            <TableCell>5</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard ISI</TableCell>
            <TableCell>5</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard BUI</TableCell>
            <TableCell>5</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Standard FWI</TableCell>
            <TableCell>5</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIOutput)
