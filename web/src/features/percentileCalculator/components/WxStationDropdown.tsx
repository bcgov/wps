import React from 'react'
import { useSelector } from 'react-redux'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField, Link } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import LaunchIcon from '@material-ui/icons/Launch'

import { selectPercentileStations } from 'app/rootReducer'
import { WEATHER_STATION_MAP_LINK } from 'utils/constants'
import { ErrorMessage } from 'components/ErrorMessage'

const useStyles = makeStyles({
  root: {
    width: '100%'
  },
  wrapper: {
    display: 'flex',
    alignItems: 'flex-start',
    minWidth: 300
  },
  mapLink: {
    marginBottom: 8
  },
  mapLabel: {
    display: 'flex'
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
  maxNumOfSelect?: number
}

const WxStationDropdown = (props: Props) => {
  const classes = useStyles()
  const {
    loading: fetchingStations,
    stations,
    stationsByCode,
    error: errorFetchingStations
  } = useSelector(selectPercentileStations)

  let isThereUnknownCode = false
  const maxNumOfSelect = props.maxNumOfSelect || 3
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
          options={autocompleteOptions}
          getOptionLabel={option => `${option.name} (${option.code})`}
          onChange={(_, options) => {
            if (options.length <= maxNumOfSelect) {
              props.onChange(options.map(s => s.code))
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
              error={isThereError}
              helperText={
                !isThereError && `Select up to ${maxNumOfSelect} weather stations.`
              }
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

      {!errorFetchingStations && isThereUnknownCode && (
        <ErrorMessage
          error="Unknown station code(s)"
          message="Unknown weather station code(s) detected."
        />
      )}
    </div>
  )
}

export default React.memo(WxStationDropdown)
