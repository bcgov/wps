import React from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import { selectFireWeatherStations } from 'app/rootReducer'

const useStyles = makeStyles({
  autocomplete: {
    width: '100%'
  },
  wrapper: {
    display: 'flex',
    alignItems: 'flex-start',
    minWidth: 300
  }
})

interface Option {
  name: string
  code: number
}

interface Props {
  className?: string
  stationCodes: number[]
  onChange: (codes: number[]) => void
}

const WxStationDropdown = (props: Props) => {
  const classes = useStyles()
  const {
    loading: fetchingStations,
    stations,
    stationsByCode,
    error: errorFetchingStations
  } = useSelector(selectFireWeatherStations)

  let isThereUnknownCode = false
  const autocompleteValue: Option[] = props.stationCodes.map(code => {
    const station = stationsByCode[code]
    if (station) {
      return { name: station.properties.name, code: station.properties.code }
    }

    isThereUnknownCode = true
    return { name: 'Unknown', code }
  })
  const isThereError =
    !fetchingStations && (Boolean(errorFetchingStations) || isThereUnknownCode)
  const autocompleteOptions: Option[] = stations.map(station => ({
    name: station.properties.name,
    code: station.properties.code
  }))

  return (
    <div className={props.className}>
      <div className={classes.wrapper}>
        <Autocomplete
          id="weather-station-dropdown"
          className={classes.autocomplete}
          data-testid="weather-station-dropdown"
          multiple
          options={autocompleteOptions}
          getOptionLabel={option => `${option.name} (${option.code})`}
          onChange={(_, options) => {
            props.onChange(options.map(s => s.code))
          }}
          size="small"
          value={autocompleteValue}
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
    </div>
  )
}

export default React.memo(WxStationDropdown)
