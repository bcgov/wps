import { FormControl, InputLabel, MenuItem, Select, SelectChangeEvent } from '@mui/material'
import { RASTER_CONFIG, RasterType } from './map/rasterConfig'

interface RasterTypeDropdownProps {
  selectedRasterType: RasterType
  setSelectedRasterType: (rasterType: RasterType) => void
}

const RasterTypeDropdown = ({ selectedRasterType, setSelectedRasterType }: RasterTypeDropdownProps) => {
  const handleChange = (event: SelectChangeEvent<RasterType>) => {
    setSelectedRasterType(event.target.value as RasterType)
  }

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
        {(Object.keys(RASTER_CONFIG) as RasterType[]).map(type => (
          <MenuItem key={type} value={type}>
            {RASTER_CONFIG[type].label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}

export default RasterTypeDropdown
