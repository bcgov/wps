import React from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField, Link } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import LaunchIcon from '@material-ui/icons/Launch'

import { Station } from 'api/stationAPI'
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
  stations: Station[]
  onStationsChange: (stations: Station[]) => void
  maxNumOfSelect?: number
}

export const WxStationDropdown = (props: Props) => {
  const classes = useStyles()
  const { stations, error } = useSelector(selectStations)
  const isError = Boolean(error)
  const maxNumOfSelect = props.maxNumOfSelect || 3

  return (
    <div className={props.className}>
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
          className={classes.root}
          data-testid="weather-station-dropdown"
          multiple
          options={stations}
          getOptionLabel={option => `${option.name} (${option.code})`}
          onChange={(_, stations) => {
            if (stations.length > maxNumOfSelect) {
              return
            }
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
              error={isError}
              helperText={!isError && `Select up to ${maxNumOfSelect} weather stations.`}
            />
          )}
        />
      </div>
      {error && <ErrorMessage error={error} context="while fetching weather stations" />}
    </div>
  )
}
