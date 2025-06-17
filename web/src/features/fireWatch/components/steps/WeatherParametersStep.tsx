import { FORM_MAX_WIDTH } from '@/features/fireWatch/components/CreateFireWatch'
import { FireWatch } from '@/features/fireWatch/interfaces'
import { Box, Step, TextField, Typography, useTheme } from '@mui/material'
import { isNull } from 'lodash'
import { SetStateAction } from 'react'

interface WeatherParametersStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
}

const WeatherParametersStep = ({ fireWatch, setFireWatch }: WeatherParametersStepProps) => {
  const theme = useTheme()

  const handleFormUpdate = (partialFireWatch: Partial<FireWatch>) => {
    const newFireWatch = { ...fireWatch, ...partialFireWatch }
    setFireWatch(newFireWatch)
  }

  return (
    <Step>
      <Box sx={{ display: 'flex', flexDirection: 'column', width: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4) }}>
        <Typography variant="h6">Step 3: Weather Parameters</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', flexDirection: 'row', pt: theme.spacing(2) }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(4) }}>
              <Typography sx={{ pb: theme.spacing(2) }} variant="body1">
                Temperature (°C){' '}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
                <TextField
                  label="Minimum"
                  size="small"
                  type="number"
                  value={isNaN(fireWatch.tempMin) ? '' : fireWatch.tempMin}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate({ tempMin: parseFloat(event.target.value) })
                  }
                  sx={{ pr: theme.spacing(2) }}
                />
                <TextField
                  label="Preferred"
                  size="small"
                  type="number"
                  value={
                    isNull(fireWatch.tempPreferred) || isNaN(fireWatch.tempPreferred) ? '' : fireWatch.tempPreferred
                  }
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate({ tempPreferred: parseFloat(event.target.value) })
                  }
                  sx={{ pr: theme.spacing(2) }}
                />
                <TextField
                  label="Maximum"
                  size="small"
                  type="number"
                  value={isNaN(fireWatch.tempMax) ? '' : fireWatch.tempMax}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate({ tempMax: parseFloat(event.target.value) })
                  }
                />
              </Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(4) }}>
            <Typography sx={{ pb: theme.spacing(2) }} variant="body1">
              Relative Humidity (%){' '}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
              <TextField
                label="Minimum"
                size="small"
                type="number"
                value={isNaN(fireWatch.rhMin) ? '' : fireWatch.rhMin}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ rhMin: parseFloat(event.target.value) })
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                label="Preferred"
                size="small"
                type="number"
                value={isNull(fireWatch.rhPreferred) || isNaN(fireWatch.rhPreferred) ? '' : fireWatch.rhPreferred}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ rhPreferred: parseFloat(event.target.value) })
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                label="Maximum"
                size="small"
                type="number"
                value={isNaN(fireWatch.rhMax) ? '' : fireWatch.rhMax}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ rhMax: parseFloat(event.target.value) })
                }
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(2) }} variant="body1">
              Wind Speed (km/h){' '}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
              <TextField
                label="Minimum"
                size="small"
                type="number"
                value={isNaN(fireWatch.windSpeedMin) ? '' : fireWatch.windSpeedMin}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ windSpeedMin: parseFloat(event.target.value) })
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                label="Preferred"
                size="small"
                type="number"
                value={
                  isNull(fireWatch.windSpeedPreferred) || isNaN(fireWatch.windSpeedPreferred)
                    ? ''
                    : fireWatch.windSpeedPreferred
                }
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ windSpeedPreferred: parseFloat(event.target.value) })
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                label="Maximum"
                size="small"
                type="number"
                value={isNaN(fireWatch.windSpeedMax) ? '' : fireWatch.windSpeedMax}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ windSpeedMax: parseFloat(event.target.value) })
                }
              />
            </Box>
          </Box>
        </Box>
      </Box>
    </Step>
  )
}

export default WeatherParametersStep
