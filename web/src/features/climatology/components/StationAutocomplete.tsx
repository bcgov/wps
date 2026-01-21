import React from 'react'
import { styled } from '@mui/material/styles'
import { useSelector } from 'react-redux'
import Autocomplete from '@mui/material/Autocomplete'
import { TextField, Link } from '@mui/material'
import LaunchIcon from '@mui/icons-material/Launch'

import { selectPercentileStations } from 'app/rootReducer'
import { WEATHER_STATION_MAP_LINK } from 'utils/constants'
import { ErrorMessage } from 'components/ErrorMessage'
import { GeoJsonStation } from 'api/stationAPI'

const PREFIX = 'StationAutocomplete'

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

interface StationOption {
  name: string
  code: number
}

interface Props {
  className?: string
  selectedStationCode: number | null
  onChange: (code: number | null) => void
}

const StationAutocomplete: React.FC<Props> = ({ className, selectedStationCode, onChange }) => {
  const { loading: fetchingStations, stations, error: errorFetchingStations } = useSelector(selectPercentileStations)

  const allStationOptions: StationOption[] = (stations as GeoJsonStation[]).map(station => ({
    name: station.properties.name,
    code: station.properties.code
  }))

  const selectedOption = allStationOptions.find(opt => opt.code === selectedStationCode) || null

  return (
    <Root className={className}>
      <div className={classes.wrapper}>
        <Link
          className={classes.mapLink}
          data-testid="launch-map-link"
          id="climatology-map-link"
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
          data-testid="climatology-station-dropdown"
          id="climatology-station-dropdown"
          options={allStationOptions}
          loading={fetchingStations}
          getOptionLabel={option => `${option.name} (${option.code})`}
          isOptionEqualToValue={(option, value) => option.code === value.code}
          onChange={(_, option) => {
            onChange(option?.code ?? null)
          }}
          value={selectedOption}
          renderInput={params => (
            <TextField
              {...params}
              label="Weather Station"
              variant="outlined"
              fullWidth
              size="small"
              error={Boolean(errorFetchingStations)}
              helperText={!errorFetchingStations && 'Select a weather station to view climatology data.'}
            />
          )}
        />
      </div>

      {errorFetchingStations && (
        <ErrorMessage error={errorFetchingStations} context="while fetching weather stations" />
      )}
    </Root>
  )
}

export default React.memo(StationAutocomplete)
