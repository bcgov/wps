import {
  TableContainer,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TextField,
  InputAdornment
} from '@material-ui/core'
import FWIStationCell from 'features/fwiCalculator/components/FWIStationCell'
import React from 'react'

const BasicFWIInput = () => {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="Basic FWI Calculation Inputs" size="small">
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
                fullWidth
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
                fullWidth
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
                fullWidth
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
                InputProps={{
                  endAdornment: <InputAdornment position="end">C°</InputAdornment>
                }}
                inputProps={{ min: 0, max: 100 }}
                fullWidth
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
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>
                }}
                inputProps={{ min: 0, max: 100 }}
                fullWidth
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
                InputProps={{
                  endAdornment: <InputAdornment position="end">km/h</InputAdornment>
                }}
                inputProps={{ min: 0, max: 100 }}
                fullWidth
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
                InputProps={{
                  endAdornment: <InputAdornment position="end">mm</InputAdornment>
                }}
                inputProps={{ min: 0, max: 100 }}
                fullWidth
                defaultValue={75}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIInput)
