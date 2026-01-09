import { FormControl, InputLabel, MenuItem, Select, SelectChangeEvent } from '@mui/material'
import { RASTER_CONFIG, RasterType } from './map/rasterConfig'

interface RasterTypeDropdownProps {
  selectedRasterType: RasterType
  setSelectedRasterType: (rasterType: RasterType) => void
  rasterDataAvailable?: boolean
}

const RasterTypeDropdown = ({ selectedRasterType, setSelectedRasterType, rasterDataAvailable = true }: RasterTypeDropdownProps) => {
  const handleChange = (event: SelectChangeEvent<RasterType>) => {
    const newValue = event.target.value as RasterType
    // Prevent selecting fire weather types when data is unavailable
    if (!rasterDataAvailable && newValue !== 'fuel') {
      return
    }
    setSelectedRasterType(newValue)
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
          <MenuItem key={type} value={type} disabled={!rasterDataAvailable && type !== 'fuel'}>
            {RASTER_CONFIG[type].label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}

export default RasterTypeDropdown
