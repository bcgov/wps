import React, { useEffect, useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { useHistory, useLocation } from 'react-router-dom'

import TimeOfInterestPicker from 'features/fireWeather/components/TimeOfInterestPicker'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { stationCodeQueryKey, timeOfInterestQueryKey } from 'utils/url'
import WxStationDropdown from 'features/fireWeather/components/WxStationDropdown'

const useStyles = makeStyles({
  form: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',

    '& fieldset, label, input': {
      color: 'white !important',
      borderColor: 'white !important',
    },
    '& .MuiChip-root': {
      background: '#f0f0f0',
    },
  },
  stationDropdown: {
    marginRight: 16,
  },
  timeOfInterest: {
    marginRight: 16,
  },
})

interface Props {
  className?: string
  codesFromQuery: number[]
  toiFromQuery: string
  openSidePanel: () => void
}

const WxDataForm = ({ codesFromQuery, toiFromQuery, openSidePanel }: Props) => {
  const classes = useStyles()
  const history = useHistory()
  const location = useLocation()

  const [selectedCodes, setSelectedCodes] = useState<number[]>(codesFromQuery)
  const [timeOfInterest, setTimeOfInterest] = useState(toiFromQuery)
  const shouldGetBtnDisabled = selectedCodes.length === 0

  useEffect(() => {
    // Update local state to match with the query url
    setSelectedCodes(codesFromQuery)
    setTimeOfInterest(toiFromQuery)
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = () => {
    // Open the side panel
    openSidePanel()

    // Update the url query with the new station codes and time of interest
    history.push({
      search:
        `${stationCodeQueryKey}=${selectedCodes.join(',')}&` +
        `${timeOfInterestQueryKey}=${timeOfInterest}`,
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
        timeOfInterest: timeOfInterest,
      })
    }
  }

  return (
    <form className={classes.form} noValidate>
      <WxStationDropdown
        className={classes.stationDropdown}
        stationCodes={selectedCodes}
        onChange={setSelectedCodes}
      />
      <TimeOfInterestPicker
        className={classes.timeOfInterest}
        timeOfInterest={timeOfInterest}
        onChange={setTimeOfInterest}
      />
      <GetWxDataButton onBtnClick={handleSubmit} disabled={shouldGetBtnDisabled} />
    </form>
  )
}

export default React.memo(WxDataForm)
