import { TableContainer, Paper, Table, TableRow, TableCell, TableBody, InputAdornment } from '@mui/material'
import { YesterdayIndices } from 'api/fwiAPI'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import FWINumberCell from 'features/fwiCalculator/components/FWINumberCell'
import YesterdayIndexCells from 'features/fwiCalculator/components/YesterdayIndices'
import React from 'react'
export interface Option {
  name: string
  code: number
}
export interface BasicFWIInputProps {
  isLoading: boolean
  input: FWIInputParameters
  yesterday?: YesterdayIndices
  setInput: React.Dispatch<React.SetStateAction<FWIInputParameters>>
}
const BasicFWIInput = ({ isLoading, input, yesterday, setInput }: BasicFWIInputProps) => {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="Basic FWI Calculation Inputs">
        <TableBody>
          <YesterdayIndexCells isLoading={isLoading} yesterdayActuals={yesterday} />
          <TableRow>
            <TableCell>Today&apos;s 1300 Temperature</TableCell>
            <FWINumberCell
              inputField={'todayTemp'}
              input={input}
              inputProps={{
                endAdornment: <InputAdornment position="end">C°</InputAdornment>
              }}
              setInput={setInput}
              isLoading={isLoading}
            />
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s 1300 Relative Humidity</TableCell>
            <FWINumberCell
              inputField={'todayRH'}
              input={input}
              inputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>
              }}
              setInput={setInput}
              isLoading={isLoading}
            />
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s 1300 Wind Speed</TableCell>
            <FWINumberCell
              inputField={'todayWindspeed'}
              input={input}
              inputProps={{
                endAdornment: <InputAdornment position="end">km/h</InputAdornment>
              }}
              setInput={setInput}
              isLoading={isLoading}
            />
          </TableRow>
          <TableRow>
            <TableCell>Today&apos;s Precipitation</TableCell>
            <FWINumberCell
              inputField={'todayPrecip'}
              input={input}
              inputProps={{
                endAdornment: <InputAdornment position="end">mm</InputAdornment>
              }}
              setInput={setInput}
              isLoading={isLoading}
            />
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default React.memo(BasicFWIInput)
