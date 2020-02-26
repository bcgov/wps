import React from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField, Tooltip } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import MapIcon from '@material-ui/icons/Map'
import IconButton from '@material-ui/core/IconButton'
import { Station } from 'api/stationAPI'
import { selectStationsReducer } from 'app/rootReducer'

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
    window.open(
      'https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=c36baf74b74a46978cf517579a9ee332',
      '_blank'
    )
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
            color="primary"
            className={classes.mapIcon}
            aria-label="directions"
            onClick={onMapIconClick}
          >
            <MapIcon />
          </IconButton>
        </Tooltip>
      </div>
      {error && <div>{error} (while fetching weather stations) </div>}
    </>
  )
}
