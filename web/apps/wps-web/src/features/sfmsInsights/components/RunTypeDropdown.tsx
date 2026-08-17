import { FormControl, InputLabel, MenuItem, Select, type SelectChangeEvent } from '@mui/material'
import { RunType } from '@wps/api/runType'

const RUN_TYPE_LABELS: Record<RunType, string> = {
  [RunType.ACTUAL]: 'Actual',
  [RunType.FORECAST]: 'Forecast'
}

interface RunTypeDropdownProps {
  selectedRunType: RunType
  setSelectedRunType: (runType: RunType) => void
}

const RunTypeDropdown = ({ selectedRunType, setSelectedRunType }: RunTypeDropdownProps) => {
  const handleChange = (event: SelectChangeEvent<RunType>) => {
    setSelectedRunType(event.target.value as RunType)
  }

  return (
    <FormControl sx={{ minWidth: 140 }}>
      <InputLabel id="sfms-run-type-label">Source</InputLabel>
      <Select
        labelId="sfms-run-type-label"
        id="sfms-run-type-select"
        value={selectedRunType}
        label="Source"
        onChange={handleChange}
      >
        {Object.values(RunType).map(runType => (
          <MenuItem key={runType} value={runType}>
            {RUN_TYPE_LABELS[runType]}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}

export default RunTypeDropdown
