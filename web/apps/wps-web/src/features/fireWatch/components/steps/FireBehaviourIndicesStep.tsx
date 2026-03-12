import OptionalHeading from '@/features/fireWatch/components/OptionalHeading'
import { FORM_MAX_WIDTH } from '@/features/fireWatch/constants'
import { FireWatch } from '@/features/fireWatch/interfaces'
import { Box, Step, TextField, Typography, useTheme } from '@mui/material'
import { isNull } from 'lodash'
import { SetStateAction } from 'react'

interface FireBehaviourIndicesStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
}

const FireBehaviourIndicesStep = ({ fireWatch, setFireWatch }: FireBehaviourIndicesStepProps) => {
  const theme = useTheme()

  const handleFormUpdate = (partialFireWatch: Partial<FireWatch>) => {
    const newFireWatch = { ...fireWatch, ...partialFireWatch }
    setFireWatch(newFireWatch)
  }

  return (
    <Step>
      <Box sx={{ display: 'flex', flexDirection: 'column', width: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4) }}>
        <Typography variant="h6">Step 5: Fire Behaviour Indices</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', flexDirection: 'row', pt: theme.spacing(2) }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(4) }}>
              <OptionalHeading>Initial Spread Index (ISI)</OptionalHeading>
              <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
                <TextField
                  required={!isNull(fireWatch.isiMax) && !isNaN(fireWatch.isiMax)}
                  label="Minimum"
                  size="small"
                  type="number"
                  value={isNull(fireWatch.isiMin) || isNaN(fireWatch.isiMin) ? '' : fireWatch.isiMin}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate({ isiMin: parseFloat(event.target.value) })
                  }
                  sx={{ pr: theme.spacing(2) }}
                />
                <TextField
                  required={!isNull(fireWatch.isiMin) && !isNaN(fireWatch.isiMin)}
                  label="Maximum"
                  size="small"
                  type="number"
                  value={isNull(fireWatch.isiMax) || isNaN(fireWatch.isiMax) ? '' : fireWatch.isiMax}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate({ isiMax: parseFloat(event.target.value) })
                  }
                />
              </Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(2) }} variant="body1">
              Head Fire Intensity (HFI){' '}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
              <TextField
                required
                label="Minimum"
                size="small"
                type="number"
                value={isNaN(fireWatch.hfiMin) ? '' : fireWatch.hfiMin}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ hfiMin: parseFloat(event.target.value) })
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                required
                label="Maximum"
                size="small"
                type="number"
                value={isNaN(fireWatch.hfiMax) ? '' : fireWatch.hfiMax}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ hfiMax: parseFloat(event.target.value) })
                }
              />
            </Box>
          </Box>
        </Box>
      </Box>
    </Step>
  )
}

export default FireBehaviourIndicesStep
