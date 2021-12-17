import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { GeoJsonStation, getStations, StationSource } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import { ErrorMessage } from 'components'
import { GridMenuOption } from 'features/fbaCalculator/components/FBATable'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

export interface FWIStationCellProps {
  stationOptions: GridMenuOption[]
}

const FWIStationCell = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  const { error, stations } = useSelector(selectFireWeatherStations)
  const allStationOptions = (stations as GeoJsonStation[]).map(station => ({
    name: station.properties.name,
    code: station.properties.code
  }))
  return (
    <React.Fragment>
      <Autocomplete
        autoHighlight={true}
        autoSelect={true}
        options={allStationOptions}
        getOptionLabel={option => `${option.name} (${option.code})`}
        renderInput={params => <TextField {...params} variant="outlined" size="small" />}
        // onChange={changeHandler}
        // disabled={props.disabled}
        value={null}
      />
      {error && <ErrorMessage error={error} context="while fetching weather stations" />}
    </React.Fragment>
  )
}
export default React.memo(FWIStationCell)
