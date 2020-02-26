import React from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import { Station } from 'api/stationAPI'
import { selectStationsReducer } from 'app/rootReducer'

const useStyles = makeStyles({
  root: {
    width: 600
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
      {error && <div>{error} (while fetching weather stations) </div>}
    </>
  )
}
