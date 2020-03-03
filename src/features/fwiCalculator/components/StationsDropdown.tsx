import React from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField, Tooltip } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import MapIcon from '@material-ui/icons/Map'
import IconButton from '@material-ui/core/IconButton'
import { Station } from 'api/stationAPI'
import { selectStationsReducer } from 'app/rootReducer'
import { WEATHER_STATION_MAP_LINK } from 'utils/constants'
import { ErrorMessage } from 'components/ErrorMessage'

const useStyles = makeStyles({
  root: {
    width: 600
  },
  mapIcon: {
    padding: 10
  },
  wrapper: {
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

  const onMapIconClick = () => {
    window.open(WEATHER_STATION_MAP_LINK, '_blank')
  }

  return (
    <>
      <div className={classes.wrapper}>
        <Autocomplete
          className={classes.root}
          data-testid="weather-station-dropdown"
          options={stations}
          getOptionLabel={option => `${option.name} (${option.code})`}
          onChange={(_, stations) => {
            props.onStationsChange(stations)
          }}
          multiple
          value={props.stations}
          renderInput={params => (
            <TextField
              {...params}
              label="Weather Stations"
              variant="outlined"
              fullWidth
              size="small"
            />
          )}
        />
        <Tooltip title="Navigate to Weather Stations Map">
          <IconButton
            data-testid="map-icon"
            className={classes.mapIcon}
            color="primary"
            aria-label="directions"
            onClick={onMapIconClick}
          >
            <MapIcon />
          </IconButton>
        </Tooltip>
      </div>
      {error && (
        <ErrorMessage message={error} when="while fetching weather stations" />
      )}
    </>
  )
}
