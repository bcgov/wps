import WPSDatePicker from "@/components/WPSDatePicker"
import { FORM_MAX_WIDTH } from "@/features/fireWatch/components/CreateFireWatch"
import { FireWatch } from "@/features/fireWatch/fireWatchApi"
import { updateFireWatch } from "@/features/fireWatch/utils"
import { Box, Step, TextField, Typography, useTheme } from "@mui/material"
import { DateTime } from "luxon"
import { SetStateAction } from "react"

interface InfoStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
}

const InfoStep = ({fireWatch, setFireWatch}: InfoStepProps) => {
  const theme = useTheme()

  const handleFormUpdate = <K extends keyof FireWatch>(key: K, value: FireWatch[K]) => {
    updateFireWatch(fireWatch, key, value, setFireWatch)
  }

  const updateBurnWindowStart = (newDate: DateTime) => {
    handleFormUpdate("burnWindowStart", newDate)
  }

  const updateBurnWindowEnd = (newDate: DateTime) => {
    handleFormUpdate("burnWindowEnd", newDate)
  }

  return (
    <Step>
      <Box sx={{display: 'flex', flexDirection: 'column', width: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4)}}>
        <Typography variant='h6'>
          Step 1: Location & Basics
        </Typography>
        <Box sx={{display: 'flex', flexDirection: 'column'}}>
          <Box sx={{display: 'flex', flexDirection: 'row', pt: theme.spacing(2)}}>
            <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: 1, pr: theme.spacing(2)}}>
              <Typography sx={{pb: theme.spacing(0.5)}} variant='body1'>Latitude</Typography>
              <TextField
                required
                size="small"
                type="number"
                value={isNaN(fireWatch.latitude) ? "" : fireWatch.latitude}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) => handleFormUpdate("latitude", parseFloat(event.target.value))}
              />
            </Box>
            <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: 1}}>
              <Typography sx={{pb: theme.spacing(0.5)}} variant='body1'>Longitude</Typography>
              <TextField
                required
                size="small"
                type="number"
                value={isNaN(fireWatch.longitude) ? "" : fireWatch.longitude}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) => handleFormUpdate("longitude", parseFloat(event.target.value))}
              />
            </Box>
          </Box>
          <Box sx={{display: 'flex', flexDirection: 'row', flexGrow: 1, pt: theme.spacing(2)}}>
            <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: 1, pr: theme.spacing(2)}}>
              <Typography sx={{pb: theme.spacing(0.5)}} variant='body1'>Burn Window Start Date</Typography>
              <WPSDatePicker
                date={fireWatch.burnWindowStart}
                label=""
                updateDate={updateBurnWindowStart}
                size="small" />
            </Box>
            <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: 1}}>
              <Typography sx={{pb: theme.spacing(0.5)}} variant='body1'>Burn Window End Date</Typography>
              <WPSDatePicker date={fireWatch.burnWindowEnd} label="" updateDate={updateBurnWindowEnd} size="small" />
            </Box>
          </Box>
          <Box sx={{display: 'flex', flexDirection: 'column', pt: theme.spacing(2)}}>
            <Typography sx={{pb: theme.spacing(0.5)}} variant='body1'>Burn Name</Typography>
            <TextField
              required
              size="small"
              value={fireWatch.title}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => handleFormUpdate("title", event.target.value)}
              />
          </Box>
          <Box sx={{display: 'flex', flexDirection: 'column', pt: theme.spacing(2)}}>
            <Typography sx={{pb: theme.spacing(0.5)}} variant='body1'>Notification Email</Typography>
            <TextField
              required
              size="small"
              value={fireWatch.contactEmail}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => handleFormUpdate("contactEmail", [event.target.value])}
              />
          </Box>
        </Box>
      </Box>
    </Step>
  )
}

export default InfoStep