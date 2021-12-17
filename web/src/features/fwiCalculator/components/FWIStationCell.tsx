import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { GeoJsonStation, getStations, StationSource } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import { ErrorMessage } from 'components'
import { GridMenuOption } from 'features/fbaCalculator/components/FBATable'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { isEqual } from 'lodash'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

export interface Option {
  name: string
  code: number
}
export interface FWIStationCellProps {
  stationOptions: GridMenuOption[]
}
const emptyLabel = 'Select a station'

const FWIStationCell = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  const { error, stations } = useSelector(selectFireWeatherStations)
  const allStationOptions: Option[] = (stations as GeoJsonStation[]).map(station => ({
    name: station.properties.name,
    code: station.properties.code
  }))

  const [selectedStation, setSelectedStation] = useState<Option | null>(null)

  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(selectedStation, value)) {
      setSelectedStation(value)
    }
  }

  return (
    <React.Fragment>
      <Autocomplete
        autoHighlight={true}
        autoSelect={true}
        options={allStationOptions}
        getOptionLabel={option => `${option.name} (${option.code})`}
        renderInput={params => (
          <TextField
            {...params}
            label={selectedStation ? '' : emptyLabel}
            variant="outlined"
            size="small"
          />
        )}
        onChange={changeHandler}
        value={selectedStation}
      />
      {error && <ErrorMessage error={error} context="while fetching weather stations" />}
    </React.Fragment>
  )
}
export default React.memo(FWIStationCell)
