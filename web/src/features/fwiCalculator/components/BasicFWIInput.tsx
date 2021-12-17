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
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import FWIStationCell from 'features/fwiCalculator/components/FWIStationCell'
import React from 'react'
export interface BasicFWIInputProps {
  input: FWIInputParameters
}
const BasicFWIInput = (props: BasicFWIInputProps) => {
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
                defaultValue={props.input.yesterdayFFMC}
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
                defaultValue={props.input.yesterdayDMC}
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
                defaultValue={props.input.yesterdayDC}
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
                defaultValue={props.input.todayTemp}
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
                defaultValue={props.input.todayRH}
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
                defaultValue={props.input.todayWindspeed}
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
                defaultValue={props.input.todayPrecip}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIInput)
