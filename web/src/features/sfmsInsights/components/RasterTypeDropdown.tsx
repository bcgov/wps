import { FormControl, InputLabel, MenuItem, Select, SelectChangeEvent } from '@mui/material'
import { FireWeatherRasterType } from './map/layerDefinitions'
import { RASTER_CONFIG } from './map/rasterConfig'

interface RasterTypeDropdownProps {
  selectedRasterType: FireWeatherRasterType
  setSelectedRasterType: (rasterType: FireWeatherRasterType) => void
}

const RasterTypeDropdown = ({ selectedRasterType, setSelectedRasterType }: RasterTypeDropdownProps) => {
  const handleChange = (event: SelectChangeEvent<FireWeatherRasterType>) => {
    setSelectedRasterType(event.target.value as FireWeatherRasterType)
  }

  const rasterTypes: FireWeatherRasterType[] = ['fwi', 'dmc', 'dc', 'ffmc', 'bui', 'isi']

  return (
    <FormControl sx={{ minWidth: 200 }}>
      <InputLabel id="raster-type-label">Raster Type</InputLabel>
      <Select
        labelId="raster-type-label"
        id="raster-type-select"
        value={selectedRasterType}
        label="Raster Type"
        onChange={handleChange}
      >
        {rasterTypes.map(type => (
          <MenuItem key={type} value={type}>
            {RASTER_CONFIG[type].label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}

export default RasterTypeDropdown
