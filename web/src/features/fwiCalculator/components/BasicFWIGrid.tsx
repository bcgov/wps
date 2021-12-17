import React from 'react'
import {
  TableContainer,
  Paper,
  Table,
  TableRow,
  TableCell,
  TableBody,
  Grid
} from '@material-ui/core'
import BasicFWIInput from 'features/fwiCalculator/components/BasicFWIInput'

const BasicFWIGrid: React.FunctionComponent = () => {
  return (
    /** Input table */
    <Grid container direction={'row'} spacing={2}>
      <Grid item xs={4}>
        <BasicFWIInput />
      </Grid>
      <Grid item xs={3}>
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
      </Grid>
    </Grid>
  )
}

export default React.memo(BasicFWIGrid)
