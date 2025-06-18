import { GeoJsonStation } from '@/api/stationAPI'
import { selectFireWatchFireCentres, selectFireWeatherStations } from '@/app/rootReducer'
import { FORM_MAX_WIDTH } from '@/features/fireWatch/components/CreateFireWatch'
import { FireWatch, FireWatchFireCentre } from '@/features/fireWatch/interfaces'
import { Autocomplete, Box, Step, TextField, Typography, useTheme } from '@mui/material'
import { isEqual, isNull } from 'lodash'
import { SetStateAction, useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { Option as StationOption } from 'utils/dropdown'

interface InfoStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
}

const InfoStep = ({ fireWatch, setFireWatch }: InfoStepProps) => {
  const theme = useTheme()
  const [stationOptions, setStationOptions] = useState<StationOption[]>([])
  const { stations } = useSelector(selectFireWeatherStations)
  const { fireCentres } = useSelector(selectFireWatchFireCentres)

  useEffect(() => {
    const allStationOptions: StationOption[] = (stations as GeoJsonStation[]).map(station => ({
      name: `${station.properties.name} (${station.properties.code})`,
      code: station.properties.code
    }))
    setStationOptions(allStationOptions)
  }, [stations])

  const handleFormUpdate = (partialFireWatch: Partial<FireWatch>) => {
    const newFireWatch = { ...fireWatch, ...partialFireWatch }
    setFireWatch(newFireWatch)
  }

  return (
    <Step>
      <Box sx={{ display: 'flex', flexDirection: 'column', width: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4) }}>
        <Typography variant="h6">Step 1: Burn Information</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Burn Name*
            </Typography>
            <TextField
              required
              size="small"
              value={fireWatch.title}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => handleFormUpdate({ title: event.target.value })}
            />
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1, pt: theme.spacing(2) }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexBasis: 0, flexGrow: 1, pr: theme.spacing(2) }}>
              <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
                Fire Centre
              </Typography>
              <Autocomplete
                autoHighlight={true}
                autoSelect={true}
                options={fireCentres}
                isOptionEqualToValue={(option, value) => isEqual(option, value)}
                getOptionLabel={option => option?.name}
                renderInput={params => (
                  <TextField
                    required
                    {...params}
                    label={isNull(fireWatch.fireCentre) ? 'Select a fire centre' : ''}
                    variant="outlined"
                    size="small"
                  />
                )}
                onChange={(_: React.SyntheticEvent<Element, Event>, newValue: FireWatchFireCentre | null) => {
                  handleFormUpdate({ fireCentre: newValue })
                }}
                value={fireWatch.fireCentre}
              />
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexBasis: 0, flexGrow: 1 }}>
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
                    label={isNull(fireWatch.station) ? 'Select a station' : ''}
                    variant="outlined"
                    size="small"
                    required
                  />
                )}
                onChange={(_: React.SyntheticEvent<Element, Event>, newValue: StationOption | null) => {
                  handleFormUpdate({ station: newValue })
                }}
                value={fireWatch.station}
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Notification Email*
            </Typography>
            <TextField
              required
              size="small"
              value={fireWatch.contactEmail}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                handleFormUpdate({ contactEmail: [event.target.value] })
              }
            />
          </Box>
        </Box>
      </Box>
    </Step>
  )
}

export default InfoStep
