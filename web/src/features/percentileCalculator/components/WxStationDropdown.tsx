import React from 'react'
import { styled } from '@mui/material/styles'
import { useSelector } from 'react-redux'
import Autocomplete from '@mui/material/Autocomplete'
import { TextField, Link } from '@mui/material'
import LaunchIcon from '@mui/icons-material/Launch'

import { selectPercentileStations } from 'app/rootReducer'
import { WEATHER_STATION_MAP_LINK } from 'utils/constants'
import { ErrorMessage } from 'components/ErrorMessage'
import { getSelectedStationOptions, Option } from 'utils/dropdown'
import { GeoJsonStation } from 'api/stationAPI'

const PREFIX = 'WxStationDropdown'

const classes = {
  root: `${PREFIX}-root`,
  wrapper: `${PREFIX}-wrapper`,
  mapLink: `${PREFIX}-mapLink`,
  mapLabel: `${PREFIX}-mapLabel`
}

const Root = styled('div')({
  [`& .${classes.root}`]: {
    width: '100%'
  },
  [`& .${classes.wrapper}`]: {
    display: 'flex',
    alignItems: 'flex-start',
    minWidth: 300
  },
  [`& .${classes.mapLink}`]: {
    marginBottom: 8
  },
  [`& .${classes.mapLabel}`]: {
    display: 'flex'
  }
})

interface Props {
  className?: string
  stationCodes: number[]
  onChange: (codes: number[]) => void
  maxNumOfSelect?: number
}

const WxStationDropdown = (props: Props) => {
  const {
    loading: fetchingStations,
    stations,
    stationsByCode,
    error: errorFetchingStations
  } = useSelector(selectPercentileStations)
  const maxNumOfSelect = props.maxNumOfSelect || 3

  const { isThereUnknownCode, selectedStationOptions } = getSelectedStationOptions(props.stationCodes, stationsByCode)
  const isThereError = !fetchingStations && (Boolean(errorFetchingStations) || isThereUnknownCode)
  const allStationOptions: Option[] = (stations as GeoJsonStation[]).map(station => ({
    name: station.properties.name,
    code: station.properties.code
  }))

  return (
    <Root className={props.className}>
      <div className={classes.wrapper}>
        <Link
          className={classes.mapLink}
          data-testid="launch-map-link"
          id="launch-map-link"
          href={WEATHER_STATION_MAP_LINK}
          target="_blank"
          rel="noopener noreferrer"
          variant="body2"
        >
          <span className={classes.mapLabel}>
            Navigate to Weather Stations Map
            <LaunchIcon fontSize="small" />
          </span>
        </Link>
      </div>

      <div className={classes.wrapper}>
        <Autocomplete
          className={classes.root}
          data-testid="weather-station-dropdown"
          id="weather-station-dropdown"
          multiple
          options={allStationOptions}
          getOptionLabel={option => `${option.name} (${option.code})`}
          onChange={(_, options) => {
            if (options.length <= maxNumOfSelect) {
              props.onChange(options.map(s => s.code))
            }
          }}
          value={selectedStationOptions}
          renderInput={params => (
            <TextField
              {...params}
              label="Weather Stations"
              variant="outlined"
              fullWidth
              size="small"
              error={isThereError}
              helperText={!isThereError && `Select up to ${maxNumOfSelect} weather stations.`}
            />
          )}
        />
      </div>

      {errorFetchingStations && (
        <ErrorMessage error={errorFetchingStations} context="while fetching weather stations" />
      )}

      {!errorFetchingStations && isThereUnknownCode && (
        <ErrorMessage error="Unknown station code(s)" message="Unknown weather station code(s) detected." />
      )}
    </Root>
  )
}

export default React.memo(WxStationDropdown)
