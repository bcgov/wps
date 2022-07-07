import React, { useState, useEffect } from 'react'
import { useSelector } from 'react-redux'
import makeStyles from '@mui/styles/makeStyles'
import { useNavigate, useLocation } from 'react-router-dom'

import TimeOfInterestPicker from 'features/fireWeather/components/TimeOfInterestPicker'
import GetWxDataButton from 'features/fireWeather/components/GetWxDataButton'
import { stationCodeQueryKey, timeOfInterestQueryKey } from 'utils/url'
import WxStationDropdown from 'features/fireWeather/components/WxStationDropdown'
import { selectStations } from 'features/stations/slices/stationsSlice'
import { selectWxDataLoading, selectFireWeatherStationsLoading, selectFireWeatherStations } from 'app/rootReducer'

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
  setSidePanelState: (show: boolean) => void
}

const WxDataForm = ({ stationCodesQuery, toiFromQuery, setSidePanelState }: Props) => {
  const classes = useStyles()
  const navigate = useNavigate()
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
      setSidePanelState(true)
      potentialCodes = `${stationCodeQueryKey}=${selectedStationsByCode.join(',')}&`
    } else {
      // Close side panel if we do not care about specific stations
      setSidePanelState(false)
    }

    // Update the url query with the new station codes and time of interest
    navigate({
      search: potentialCodes + `${timeOfInterestQueryKey}=${timeOfInterest}`
    })
  }

  return (
    <form className={classes.form} noValidate>
      <WxStationDropdown className={classes.stationDropdown} stationCodes={selectedStationsByCode} />
      <TimeOfInterestPicker
        className={classes.timeOfInterest}
        timeOfInterest={timeOfInterest}
        onChange={setTimeOfInterest}
      />
      <GetWxDataButton
        onBtnClick={handleSubmit}
        selector={hasSelectedCodes ? selectWxDataLoading : selectFireWeatherStationsLoading}
      />
    </form>
  )
}

export default React.memo(WxDataForm)
