import React from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField, Link } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import LaunchIcon from '@material-ui/icons/Launch'

import { selectStations } from 'app/rootReducer'
import { WEATHER_STATION_MAP_LINK } from 'utils/constants'
import { ErrorMessage } from 'components/ErrorMessage'

const useStyles = makeStyles({
  root: {
    width: '100%'
  },
  wrapper: {
    display: 'flex',
    alignItems: 'flex-start'
  },
  mapLink: {
    marginBottom: 8
  },
  mapLabel: {
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
  const classes = useStyles()
  const { stations, stationsByCode, error: errorFetchingStations } = useSelector(
    selectStations
  )
  let isThereInvalidCode = false
  const maxNumOfSelect = props.maxNumOfSelect || 3
  const autocompleteValue = props.stationCodes.map(code => {
    const station = stationsByCode[code]
    if (station) {
      return station
    }

    isThereInvalidCode = true
    return { name: 'Invalid', code }
  })
  const isError = Boolean(errorFetchingStations) || isThereInvalidCode

  return (
    <div className={props.className}>
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
          options={stations}
          getOptionLabel={option => `${option.name} (${option.code})`}
          onChange={(_, stations) => {
            if (stations.length <= maxNumOfSelect) {
              props.onChange(stations.map(s => s.code))
            }
          }}
          value={autocompleteValue}
          renderInput={params => (
            <TextField
              {...params}
              label="Weather Stations"
              variant="outlined"
              fullWidth
              size="small"
              error={isError}
              helperText={!isError && `Select up to ${maxNumOfSelect} weather stations.`}
            />
          )}
        />
      </div>

      {errorFetchingStations && (
        <ErrorMessage
          error={errorFetchingStations}
          context="while fetching weather stations"
        />
      )}

      {isThereInvalidCode && (
        <ErrorMessage
          error="Invalid code"
          message="Invalid weather station code(s) detected."
        />
      )}
    </div>
  )
}

export default React.memo(WxStationDropdown)
