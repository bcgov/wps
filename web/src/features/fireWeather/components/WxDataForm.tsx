import React, { Dispatch, SetStateAction } from 'react'
import { useSelector } from 'react-redux'
import { makeStyles } from '@material-ui/core/styles'
import { useHistory } from 'react-router-dom'

import TimeOfInterestPicker from 'features/fireWeather/components/TimeOfInterestPicker'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { stationCodeQueryKey, timeOfInterestQueryKey } from 'utils/url'
import WxStationDropdown from 'features/fireWeather/components/WxStationDropdown'
import { selectFireWeatherStations } from 'app/rootReducer'
import { selectStation, selectStations } from 'features/stations/slices/stationsSlice'


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
  timeOfInterestQuery: string
  setSelectedTimeOfInterest: Dispatch<SetStateAction<string>>
  openSidePanel: () => void
}

const WxDataForm = ({
  stationCodesQuery,
  timeOfInterestQuery,
  setSelectedTimeOfInterest,
  openSidePanel
}: Props) => {
  const classes = useStyles()
  const history = useHistory()
  const {
    selectedStationsByCode
  } = useSelector(selectFireWeatherStations)

  selectStations(stationCodesQuery)
  const shouldGetBtnDisabled = selectedStationsByCode.length === 0

  const handleSubmit = () => {
    // Open the side panel
    openSidePanel()

    // Update the url query with the new station codes and time of interest
    history.push({
      search:
        `${stationCodeQueryKey}=${selectedStationsByCode.join(',')}&` +
        `${timeOfInterestQueryKey}=${timeOfInterestQuery}`
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
        timeOfInterest: timeOfInterestQuery
      })
    }
  }

  return (
    <form className={classes.form} noValidate>
      <WxStationDropdown
        className={classes.stationDropdown}
        stationCodes={selectedStationsByCode}
        onChange={selectStation}
      />
      <TimeOfInterestPicker
        className={classes.timeOfInterest}
        timeOfInterest={timeOfInterestQuery}
        onChange={setSelectedTimeOfInterest}
      />
      <GetWxDataButton onBtnClick={handleSubmit} disabled={shouldGetBtnDisabled} />
    </form>
  )
}

export default React.memo(WxDataForm)
