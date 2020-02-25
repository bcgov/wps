import React, { ChangeEvent } from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField } from '@material-ui/core'

import { Station } from 'api/stationAPI'
import { selectStationsReducer } from 'app/rootReducer'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    width: 300
  }
})

interface Props {
  onStationChange: (station: Station | null) => void
}

export const WeatherStationsDropdown = (props: Props) => {
  const classes = useStyles()
  const { stations, error } = useSelector(selectStationsReducer)
  const onChange = (e: ChangeEvent<{}>, s: Station | null) => {
    props.onStationChange(s)
  }

  return (
    <>
      <Autocomplete
        className={classes.root}
        data-testid="weather-station-dropdown"
        options={stations}
        getOptionLabel={option => `${option.name}(${option.code})`}
        onChange={onChange}
        renderInput={params => (
          <TextField
            {...params}
            label="Weather Stations"
            variant="outlined"
            fullWidth
          />
        )}
      />
      {error && <div>{error} (while fetching weather stations) </div>}
    </>
  )
}
