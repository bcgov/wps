import { FireWatch } from "@/features/fireWatch/fireWatchApi"
import { Box, Step, TextField, Typography, useTheme } from "@mui/material"
import { SetStateAction } from "react"
import { updateFireWatch } from "@/features/fireWatch/utils"
import { FORM_MAX_WIDTH } from "@/features/fireWatch/components/CreateFireWatch"

interface FireBehaviourIndicesStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
}

const FireBehvaiourIndicesStep = ({fireWatch, setFireWatch}: FireBehaviourIndicesStepProps) => {
  const theme = useTheme()

  const handleFormUpdate = <K extends keyof FireWatch>(key: K, value: FireWatch[K]) => {
    updateFireWatch(fireWatch, key, value, setFireWatch)
  }

  return (
    <Step>
      <Box sx={{ display: 'flex', flexDirection: 'column', width: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4) }}>
        <Typography variant="h6">Step 5: Fire Behaviour Indices</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', flexDirection: 'row', pt: theme.spacing(2) }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(4) }}>
              <Typography sx={{ pb: theme.spacing(2) }} variant="body1">
                Initial Spread Index (ISI){' '}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
                <TextField
                  label="Minimum"
                  size="small"
                  type="number"
                  value={isNaN(fireWatch.isiMin) ? '' : fireWatch.isiMin}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate('isiMin', parseFloat(event.target.value))
                  }
                  sx={{ pr: theme.spacing(2) }}
                />
                <TextField
                  label="Preferred"
                  size="small"
                  type="number"
                  value={isNaN(fireWatch.isiPreferred) ? '' : fireWatch.isiPreferred}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate('isiPreferred', parseFloat(event.target.value))
                  }
                  sx={{ pr: theme.spacing(2) }}
                />
                <TextField
                  label="Maximum"
                  size="small"
                  type="number"
                  value={isNaN(fireWatch.isiMax) ? '' : fireWatch.isiMax}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate('isiMax', parseFloat(event.target.value))
                  }
                />
              </Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(4) }}>
            <Typography sx={{ pb: theme.spacing(2) }} variant="body1">
              Buildup Index (BUI){' '}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
              <TextField
                label="Minimum"
                size="small"
                type="number"
                value={isNaN(fireWatch.buiMin) ? '' : fireWatch.buiMin}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate('buiMin', parseFloat(event.target.value))
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                label="Preferred"
                size="small"
                type="number"
                value={isNaN(fireWatch.buiPreferred) ? '' : fireWatch.buiPreferred}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate('buiPreferred', parseFloat(event.target.value))
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                label="Maximum"
                size="small"
                type="number"
                value={isNaN(fireWatch.buiMax) ? '' : fireWatch.buiMax}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate('buiMax', parseFloat(event.target.value))
                }
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(2) }} variant="body1">
              Head Fire Intensity (HFI){' '}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
              <TextField
                label="Minimum"
                size="small"
                type="number"
                value={isNaN(fireWatch.hfiMin) ? '' : fireWatch.hfiMin}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate('hfiMin', parseFloat(event.target.value))
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                label="Preferred"
                size="small"
                type="number"
                value={isNaN(fireWatch.hfiPreferred) ? '' : fireWatch.hfiPreferred}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate('hfiPreferred', parseFloat(event.target.value))
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                label="Maximum"
                size="small"
                type="number"
                value={isNaN(fireWatch.hfiMax) ? '' : fireWatch.hfiMax}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate('hfiMax', parseFloat(event.target.value))
                }
              />
            </Box>
          </Box>
        </Box>
      </Box>
    </Step>
  )
}

export default FireBehvaiourIndicesStep