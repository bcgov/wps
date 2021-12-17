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
import { getStations, StationSource, GeoJsonStation } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import { ErrorMessage } from 'components'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import FWIStationCell from 'features/fwiCalculator/components/FWIStationCell'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
export interface Option {
  name: string
  code: number
}
export interface BasicFWIInputProps {
  input: FWIInputParameters
  setInput: React.Dispatch<React.SetStateAction<FWIInputParameters>>
}
const BasicFWIInput = ({ input, setInput }: BasicFWIInputProps) => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  const { stations, error } = useSelector(selectFireWeatherStations)
  const allStationOptions: Option[] = (stations as GeoJsonStation[]).map(station => ({
    name: station.properties.name,
    code: station.properties.code
  }))

  return (
    <TableContainer component={Paper}>
      <Table aria-label="Basic FWI Calculation Inputs" size="small">
        <TableHead>
          <TableRow>
            <TableCell>Station Name</TableCell>
            <TableCell>
              <FWIStationCell
                stationOptions={allStationOptions}
                input={input}
                setInput={setInput}
              />
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
                defaultValue={input.yesterdayFFMC}
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
                defaultValue={input.yesterdayDMC}
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
                defaultValue={input.yesterdayDC}
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
                defaultValue={input.todayTemp}
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
                defaultValue={input.todayRH}
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
                defaultValue={input.todayWindspeed}
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
                defaultValue={input.todayPrecip}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
      {error && <ErrorMessage error={error} context="while fetching weather stations" />}
    </TableContainer>
  )
}

export default React.memo(BasicFWIInput)
