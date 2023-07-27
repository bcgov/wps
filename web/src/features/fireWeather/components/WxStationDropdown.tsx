import React, { useEffect } from 'react'
import { styled } from '@mui/material/styles'
import { useSelector, useDispatch } from 'react-redux'
import { useLocation } from 'react-router-dom'
import Autocomplete from '@mui/material/Autocomplete'
import { TextField } from '@mui/material'

import { selectFireWeatherStations } from 'app/rootReducer'
import { getStationCodesFromUrl } from 'utils/url'
import { getSelectedStationOptions } from 'utils/dropdown'
import { GeoJsonStation } from 'api/stationAPI'
import { selectStations } from 'features/stations/slices/stationsSlice'

const PREFIX = 'WxStationDropdown'

const classes = {
  autocomplete: `${PREFIX}-autocomplete`,
  wrapper: `${PREFIX}-wrapper`
}

const Root = styled('div')({
  [`& .${classes.autocomplete}`]: {
    width: '100%'
  },
  [`& .${classes.wrapper}`]: {
    display: 'flex',
    alignItems: 'flex-start',
    minWidth: 300
  }
})

export interface Option {
  name: string
  code: number
}

interface Props {
  className?: string
  stationCodes: number[]
}

const WxStationDropdown = (props: Props) => {
  const dispatch = useDispatch()
  const location = useLocation()
  const { selectedStationsByCode } = useSelector(selectFireWeatherStations)

  const {
    loading: fetchingStations,
    stations,
    stationsByCode,
    error: errorFetchingStations
  } = useSelector(selectFireWeatherStations)

  const { isThereUnknownCode, selectedStationOptions } = getSelectedStationOptions(
    selectedStationsByCode,
    stationsByCode
  )
  const isThereError = !fetchingStations && (Boolean(errorFetchingStations) || isThereUnknownCode)
  const allStationOptions: Option[] = (stations as GeoJsonStation[]).map((station: GeoJsonStation) => ({
    name: station.properties.name,
    code: station.properties.code
  }))

  useEffect(() => {
    const codesFromQuery = getStationCodesFromUrl(location.search)
    if (codesFromQuery.length > 0) {
      dispatch(selectStations(codesFromQuery))
    }
  }, [dispatch, location])

  return (
    <Root className={props.className}>
      <div className={classes.wrapper}>
        <Autocomplete
          id="weather-station-dropdown"
          className={classes.autocomplete}
          data-testid="weather-station-dropdown"
          multiple
          options={allStationOptions}
          getOptionLabel={option => `${option.name} (${option.code})`}
          isOptionEqualToValue={(option, value) => option.code === value.code}
          onChange={(_, options) => {
            dispatch(selectStations(options.map(s => s.code)))
          }}
          size="small"
          value={selectedStationOptions}
          renderInput={params => (
            <TextField
              {...params}
              label="Weather Stations"
              variant="outlined"
              fullWidth
              size="small"
              error={isThereError}
            />
          )}
        />
      </div>
    </Root>
  )
}

export default React.memo(WxStationDropdown)
