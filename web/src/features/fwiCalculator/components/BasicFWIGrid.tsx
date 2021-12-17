import React from 'react'
import {
  TableContainer,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TextField
} from '@material-ui/core'
import { FWIStationCell } from 'features/fwiCalculator/components/FWIStationCell'

export const BasicFWIGrid: React.FunctionComponent = () => {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="Basic FWI Calculation Inputs">
        <TableHead>
          <TableRow>
            <TableCell>Station Name</TableCell>
            <TableCell>
              <FWIStationCell />
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>Yesterday&apos;s FFMC</TableCell>
            <TableCell>
              <TextField
                type="number"
                inputMode="numeric"
                size="small"
                variant="outlined"
                inputProps={{ min: 0, max: 100 }}
                defaultValue={20}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Yesterday&apos;s DMC</TableCell>
            <TableCell>
              <TextField
                type="number"
                inputMode="numeric"
                size="small"
                variant="outlined"
                inputProps={{ min: 0, max: 100 }}
                defaultValue={11}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Yesterday&apos;s DC</TableCell>
            <TableCell>
              <TextField
                type="number"
                inputMode="numeric"
                size="small"
                variant="outlined"
                inputProps={{ min: 0, max: 100 }}
                defaultValue={5}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s 1300 Temperature</TableCell>
            <TableCell>
              <TextField
                type="number"
                inputMode="numeric"
                size="small"
                variant="outlined"
                inputProps={{ min: 0, max: 100 }}
                defaultValue={15}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s 1300 Relative Humidity</TableCell>
            <TableCell>
              <TextField
                type="number"
                inputMode="numeric"
                size="small"
                variant="outlined"
                inputProps={{ min: 0, max: 100 }}
                defaultValue={80}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s 1300 Wind Speed</TableCell>
            <TableCell>
              <TextField
                type="number"
                inputMode="numeric"
                size="small"
                variant="outlined"
                inputProps={{ min: 0, max: 100 }}
                defaultValue={8}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Precipitation</TableCell>
            <TableCell>
              <TextField
                type="number"
                inputMode="numeric"
                size="small"
                variant="outlined"
                inputProps={{ min: 0, max: 100 }}
                defaultValue={75}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}
