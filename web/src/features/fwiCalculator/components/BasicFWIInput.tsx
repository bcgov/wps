import {
  TableContainer,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  InputAdornment
} from '@material-ui/core'
import { getStations, StationSource, GeoJsonStation } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import { ErrorMessage } from 'components'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import FWINumberCell from 'features/fwiCalculator/components/FWINumberCell'
import FWIStationCell from 'features/fwiCalculator/components/FWIStationCell'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
export interface Option {
  name: string
  code: number
}
export interface BasicFWIInputProps {
  isLoading: boolean
  input: FWIInputParameters
  setInput: React.Dispatch<React.SetStateAction<FWIInputParameters>>
}
const BasicFWIInput = ({ isLoading, input, setInput }: BasicFWIInputProps) => {
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
                isLoading={isLoading}
              />
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>Yesterday&apos;s FFMC</TableCell>
            <FWINumberCell
              inputField={'yesterdayFFMC'}
              input={input}
              setInput={setInput}
              isLoading={isLoading}
            />
          </TableRow>
          <TableRow>
            <TableCell>Yesterday&apos;s DMC</TableCell>
            <FWINumberCell
              inputField={'yesterdayDMC'}
              input={input}
              setInput={setInput}
              isLoading={isLoading}
            />
          </TableRow>
          <TableRow>
            <TableCell>Yesterday&apos;s DC</TableCell>
            <FWINumberCell
              inputField={'yesterdayDC'}
              input={input}
              inputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>
              }}
              setInput={setInput}
              isLoading={isLoading}
            />
          </TableRow>
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
      {error && <ErrorMessage error={error} context="while fetching weather stations" />}
    </TableContainer>
  )
}

export default React.memo(BasicFWIInput)
