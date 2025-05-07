import { GeoJsonStation, Station } from '@/api/stationAPI'
import { selectFireWeatherStations } from '@/app/rootReducer'
import WPSDatePicker from '@/components/WPSDatePicker'
import { FORM_MAX_WIDTH } from '@/features/fireWatch/components/CreateFireWatch'
import { FireWatch } from '@/features/fireWatch/fireWatchApi'
import { updateFireWatch } from '@/features/fireWatch/utils'
import { Autocomplete, Box, Step, TextField, Typography, useTheme } from '@mui/material'
import { isEqual, isNull } from 'lodash'
import { DateTime } from 'luxon'
import { SetStateAction, useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { Option as StationOption } from 'utils/dropdown'

interface InfoStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
}

const EMPTY_LABEL = 'Select a station'

const InfoStep = ({ fireWatch, setFireWatch }: InfoStepProps) => {
  const theme = useTheme()
  const [stationOptions, setStationOptions] = useState<StationOption[]>([])
  const { stations } = useSelector(selectFireWeatherStations)

  useEffect(() => {
    const allStationOptions: StationOption[] = (stations as GeoJsonStation[]).map(station => ({
      name: `${station.properties.name} (${station.properties.code})`,
      code: station.properties.code
    }))
    setStationOptions(allStationOptions)
  }, [stations])

  const handleFormUpdate = <K extends keyof FireWatch>(key: K, value: FireWatch[K]) => {
    updateFireWatch(fireWatch, key, value, setFireWatch)
  }

  const updateBurnWindowStart = (newDate: DateTime) => {
    handleFormUpdate('burnWindowStart', newDate)
  }

  const updateBurnWindowEnd = (newDate: DateTime) => {
    handleFormUpdate('burnWindowEnd', newDate)
  }

  return (
    <Step>
      <Box sx={{ display: 'flex', flexDirection: 'column', width: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4) }}>
        <Typography variant="h6">Step 1: Burn Information</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Burn Name
            </Typography>
            <TextField
              required
              size="small"
              value={fireWatch.title}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => handleFormUpdate('title', event.target.value)}
            />
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1, pt: theme.spacing(2) }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pr: theme.spacing(2) }}>
              <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
                Burn Window Start Date
              </Typography>
              <WPSDatePicker
                date={fireWatch.burnWindowStart}
                label=""
                updateDate={updateBurnWindowStart}
                size="small"
              />
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
              <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
                Burn Window End Date
              </Typography>
              <WPSDatePicker date={fireWatch.burnWindowEnd} label="" updateDate={updateBurnWindowEnd} size="small" />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Reference Weather Station
            </Typography>
            <Autocomplete
              autoHighlight={true}
              autoSelect={true}
              options={stationOptions}
              isOptionEqualToValue={(option, value) => isEqual(option, value)}
              getOptionLabel={option => option?.name}
              renderInput={params => (
                <TextField
                  {...params}
                  label={isNull(fireWatch.station) ? EMPTY_LABEL : ''}
                  variant="outlined"
                  size="small"
                />
              )}
              onChange={(_: React.SyntheticEvent<Element, Event>, newValue: StationOption | null) => {
                handleFormUpdate('station', newValue)
              }}
              value={fireWatch.station}
            />
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Notification Email
            </Typography>
            <TextField
              required
              size="small"
              value={fireWatch.contactEmail}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                handleFormUpdate('contactEmail', [event.target.value])
              }
            />
          </Box>
        </Box>
      </Box>
    </Step>
  )
}

export default InfoStep
