import React from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField, Link } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import LaunchIcon from '@material-ui/icons/Launch'

import { Station } from 'api/stationAPI'
import { selectStationsReducer } from 'app/rootReducer'
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
  stations: Station[]
  onStationsChange: (stations: Station[]) => void
}

export const WeatherStationsDropdown = (props: Props) => {
  const classes = useStyles()
  const { stations, error } = useSelector(selectStationsReducer)

  return (
    <>
      <div className={classes.wrapper}>
        <Link
          className={classes.mapLink}
          data-testid="launch-map-link"
          href={WEATHER_STATION_MAP_LINK}
          target="_blank"
          rel="noopener"
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
          data-testid="weather-station-dropdown"
          className={classes.root}
          multiple
          options={stations}
          getOptionLabel={option => `${option.name} (${option.code})`}
          onChange={(_, stations) => {
            props.onStationsChange(stations)
          }}
          value={props.stations}
          renderInput={params => (
            <TextField
              {...params}
              label="Weather Stations"
              variant="outlined"
              fullWidth
              size="small"
              helperText="Select up to 3 weather stations."
            />
          )}
        />
      </div>
      {error && <ErrorMessage message={error} when="while fetching weather stations" />}
    </>
  )
}
