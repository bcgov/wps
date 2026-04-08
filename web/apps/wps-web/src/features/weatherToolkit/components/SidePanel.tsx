import { ModelRunHour, ModelType } from '@/features/weatherToolkit/weatherToolkitTypes'
import { CalendarMonthOutlined, LayersOutlined, ShowChart } from '@mui/icons-material'
import { FormControl, InputLabel, MenuItem, Select, Typography } from '@mui/material'
import { Box } from '@mui/system'
import { DatePicker } from '@mui/x-date-pickers'
import { theme } from '@wps/ui/theme'
import { DateTime } from 'luxon'

interface SidePanelProps {
  model: ModelType
  setModel: React.Dispatch<React.SetStateAction<ModelType>>
  modelRunDate: DateTime
  setModelRunDate: React.Dispatch<React.SetStateAction<DateTime>>
  modelRunHour: ModelRunHour
  setModelRunHour: React.Dispatch<React.SetStateAction<ModelRunHour>>
}

const SidePanel = ({
  model,
  setModel,
  modelRunDate,
  setModelRunDate,
  modelRunHour,
  setModelRunHour
}: SidePanelProps) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', width: '320px', p: 3, bgcolor: '#FCFDFE' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <ShowChart sx={{ color: theme.palette.primary.main, fontSize: 28 }} />
        <Typography variant="h5" sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}>
          4-Panel Charts
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <CalendarMonthOutlined sx={{ color: 'text.secondary', fontSize: 20 }} />
        <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
          Time
        </Typography>
      </Box>
      <DatePicker
        label="Model Run Date (UTC)"
        value={modelRunDate}
        onChange={newValue => {
          if (newValue) setModelRunDate(newValue)
        }}
        sx={{ mb: 2, width: '100%' }}
        maxDate={DateTime.utc()}
      />
      <FormControl fullWidth sx={{ mb: 4 }}>
        <InputLabel id="model-run-hour-label">Model Run Hour</InputLabel>
        <Select
          labelId="model-run-hour-label"
          value={modelRunHour}
          label="Model Run Hour"
          onChange={e => setModelRunHour(e.target.value as ModelRunHour)}
          sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}
        >
          <MenuItem value={ModelRunHour.ZERO}>00Z</MenuItem>
          <MenuItem value={ModelRunHour.TWELVE}>12Z</MenuItem>
        </Select>
      </FormControl>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <LayersOutlined sx={{ color: 'text.secondary', fontSize: 20 }} />
        <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
          Data Configuration
        </Typography>
      </Box>
      <FormControl fullWidth>
        <InputLabel id="weather-model-label">Weather Model</InputLabel>
        <Select
          labelId="weather-model-label"
          value={model}
          label="Weather Model"
          onChange={e => setModel(e.target.value as ModelType)}
          sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}
        >
          <MenuItem value={ModelType.GDPS}>GDPS</MenuItem>
          <MenuItem value={ModelType.RDPS}>RDPS</MenuItem>
        </Select>
      </FormControl>
    </Box>
  )
}

export default SidePanel
