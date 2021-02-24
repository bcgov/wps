import React, { useEffect, useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { useHistory, useLocation } from 'react-router-dom'

import WxStationDropdown from 'features/stations/components/WxStationDropdown'
import TimeOfInterestPicker from 'features/fireWeather/components/TimeOfInterestPicker'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { stationCodeQueryKey, timeOfInterestQueryKey } from 'utils/url'

const useStyles = makeStyles({
  stationDropdown: {
    marginBottom: 10
  }
})

interface Props {
  codesFromQuery: number[]
  toiFromQuery: string
}

const WxDataForm = ({ codesFromQuery, toiFromQuery }: Props) => {
  const classes = useStyles()
  const history = useHistory()
  const location = useLocation()

  const [selectedCodes, setSelectedCodes] = useState<number[]>(codesFromQuery)
  const [timeOfInterestISO, setTimeOfInterestISO] = useState(toiFromQuery)
  const shouldGetBtnDisabled = selectedCodes.length === 0

  useEffect(() => {
    // Update local state to match with the query url
    setSelectedCodes(codesFromQuery)
    setTimeOfInterestISO(toiFromQuery)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = () => {
    // Update the url query with the new station codes
    history.push({
      search:
        `${stationCodeQueryKey}=${selectedCodes.join(',')}&` +
        `${timeOfInterestQueryKey}=${timeOfInterestISO}`
    })

    // Create matomo event
    // NOTE: This section is proof of concept - strongly consider re-factoring when adding other events.
    // TODO: Re-evaluate this way of implementing Matomo once we know more about it.
    if (window._mtm) {
      // Create event, and push list of stations to the matomo data layer.
      // see: https://developer.matomo.org/guides/tagmanager/integration-plugin#supporting-the-data-layer
      window._mtm.push({
        event: 'getWeatherData',
        stationCodes: selectedCodes,
        timeOfInterest: timeOfInterestISO
      })
    }
  }

  return (
    <form noValidate>
      <WxStationDropdown
        className={classes.stationDropdown}
        stationCodes={selectedCodes}
        onChange={setSelectedCodes}
      />
      <TimeOfInterestPicker
        timeOfInterestISO={timeOfInterestISO}
        onChange={setTimeOfInterestISO}
      />
      <GetWxDataButton onBtnClick={handleSubmit} disabled={shouldGetBtnDisabled} />
    </form>
  )
}

export default React.memo(WxDataForm)
