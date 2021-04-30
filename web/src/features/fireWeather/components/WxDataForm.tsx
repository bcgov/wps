import React, { useState, useEffect } from 'react'
import { useSelector } from 'react-redux'
import { makeStyles } from '@material-ui/core/styles'
import { useHistory, useLocation } from 'react-router-dom'

import TimeOfInterestPicker from 'features/fireWeather/components/TimeOfInterestPicker'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { stationCodeQueryKey, timeOfInterestQueryKey } from 'utils/url'
import WxStationDropdown from 'features/fireWeather/components/WxStationDropdown'
import { selectStations } from 'features/stations/slices/stationsSlice'
import {
  selectWxDataLoading,
  selectFireWeatherStationsLoading,
  selectFireWeatherStations
} from 'app/rootReducer'

const useStyles = makeStyles({
  form: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',

    '& fieldset, label, input': {
      color: 'white !important',
      borderColor: 'white !important'
    },
    '& .MuiChip-root': {
      background: '#f0f0f0'
    }
  },
  stationDropdown: {
    marginRight: 16
  },
  timeOfInterest: {
    marginRight: 16
  }
})

interface Props {
  className?: string
  stationCodesQuery: number[]
  toiFromQuery: string
  shouldOpenSidePanel: (openOrClose: boolean) => void
}

const WxDataForm = ({ stationCodesQuery, toiFromQuery, shouldOpenSidePanel }: Props) => {
  const classes = useStyles()
  const history = useHistory()
  const location = useLocation()

  const { selectedStationsByCode } = useSelector(selectFireWeatherStations)

  selectStations(stationCodesQuery)

  const [timeOfInterest, setTimeOfInterest] = useState(toiFromQuery)
  const hasSelectedCodes = selectedStationsByCode.length > 0

  useEffect(() => {
    // Update local state to match with the query url
    selectStations(selectedStationsByCode)
    setTimeOfInterest(toiFromQuery)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = () => {
    let potentialCodes = ''
    if (hasSelectedCodes) {
      // Open the side panel
      shouldOpenSidePanel(true)
      potentialCodes = `${stationCodeQueryKey}=${selectedStationsByCode.join(',')}&`
    } else {
      // Close side panel if we do not care about specific stations
      shouldOpenSidePanel(false)
    }

    // Update the url query with the new station codes and time of interest
    history.push({
      search: potentialCodes + `${timeOfInterestQueryKey}=${timeOfInterest}`
    })

    // Create matomo event
    // NOTE: This section is proof of concept - strongly consider re-factoring when adding other events.
    // TODO: Re-evaluate this way of implementing Matomo once we know more about it.
    if (window._mtm) {
      // Create event, and push list of stations to the matomo data layer.
      // see: https://developer.matomo.org/guides/tagmanager/integration-plugin#supporting-the-data-layer
      window._mtm.push({
        event: 'getWeatherData',
        stationCodes: selectedStationsByCode,
        timeOfInterest: timeOfInterest
      })
    }
  }

  return (
    <form className={classes.form} noValidate>
      <WxStationDropdown
        className={classes.stationDropdown}
        stationCodes={selectedStationsByCode}
      />
      <TimeOfInterestPicker
        className={classes.timeOfInterest}
        timeOfInterest={timeOfInterest}
        onChange={setTimeOfInterest}
      />
      <GetWxDataButton
        onBtnClick={handleSubmit}
        selector={
          hasSelectedCodes ? selectWxDataLoading : selectFireWeatherStationsLoading
        }
      />
    </form>
  )
}

export default React.memo(WxDataForm)
