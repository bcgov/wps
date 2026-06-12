export const SFMSNG_RASTER_TYPES = [
  'fwi',
  'dmc',
  'dc',
  'ffmc',
  'bui',
  'isi',
  'temperature',
  'relative_humidity',
  'wind_speed',
  'wind_direction',
  'precipitation'
]

export type SFMSNGRasterType = (typeof SFMSNG_RASTER_TYPES)[number]
export type RasterType = SFMSNGRasterType | 'fuel'

export interface ColorBreak {
  min: number
  max: number | null
  color: string
  label: string
}

export interface FuelTypeColorMapping {
  value: number
  fuelCode: string
  color: string
  rgb: [number, number, number]
}

export interface RasterConfig {
  label: string
  colorBreaks: ColorBreak[]
}

export const FWI_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 8, color: 'rgb(0, 0, 255)', label: '0-8' },
  { min: 8, max: 17, color: 'rgb(0, 127, 255)', label: '8-17' },
  { min: 17, max: 27, color: 'rgb(0, 255, 0)', label: '17-27' },
  { min: 27, max: 38, color: 'rgb(255, 255, 0)', label: '27-38' },
  { min: 38, max: 47, color: 'rgb(255, 170, 0)', label: '38-47' },
  { min: 47, max: null, color: 'rgb(255, 0, 0)', label: '47+' }
]

export const DMC_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 35, color: 'rgb(0, 0, 255)', label: '0-35' },
  { min: 35, max: 50, color: 'rgb(0, 255, 0)', label: '35-50' },
  { min: 50, max: 75, color: 'rgb(255, 255, 0)', label: '50-75' },
  { min: 75, max: 100, color: 'rgb(255, 170, 0)', label: '75-100' },
  { min: 100, max: null, color: 'rgb(255, 0, 0)', label: '100+' }
]

export const DC_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 150, color: 'rgb(0, 0, 255)', label: '0-150' },
  { min: 150, max: 250, color: 'rgb(0, 127, 255)', label: '150-250' },
  { min: 250, max: 350, color: 'rgb(0, 255, 0)', label: '250-350' },
  { min: 350, max: 500, color: 'rgb(255, 255, 0)', label: '350-500' },
  { min: 500, max: 750, color: 'rgb(255, 170, 0)', label: '500-750' },
  { min: 750, max: null, color: 'rgb(255, 0, 0)', label: '750+' }
]

export const BUI_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 50, color: 'rgb(0, 0, 255)', label: '0-50' },
  { min: 50, max: 90, color: 'rgb(0, 127, 255)', label: '50-90' },
  { min: 90, max: 140, color: 'rgb(0, 255, 0)', label: '90-140' },
  { min: 140, max: 160, color: 'rgb(255, 255, 0)', label: '140-160' },
  { min: 160, max: 200, color: 'rgb(255, 170, 0)', label: '160-200' },
  { min: 200, max: null, color: 'rgb(255, 0, 0)', label: '200+' }
]

export const FFMC_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 25, color: 'rgb(210, 255, 255)', label: '0-25' },
  { min: 25, max: 35, color: 'rgb(160, 210, 255)', label: '25-35' },
  { min: 35, max: 45, color: 'rgb(0, 127, 255)', label: '35-45' },
  { min: 45, max: 55, color: 'rgb(0, 0, 255)', label: '45-55' },
  { min: 55, max: 65, color: 'rgb(0, 255, 0)', label: '55-65' },
  { min: 65, max: 75, color: 'rgb(0, 127, 0)', label: '65-75' },
  { min: 75, max: 85, color: 'rgb(255, 255, 0)', label: '75-85' },
  { min: 85, max: 90, color: 'rgb(255, 170, 0)', label: '85-90' },
  { min: 90, max: 93, color: 'rgb(255, 0, 0)', label: '90-93' },
  { min: 93, max: 96, color: 'rgb(190, 50, 0)', label: '93-96' },
  { min: 96, max: null, color: 'rgb(127, 0, 0)', label: '96+' }
]

export const ISI_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 4, color: 'rgb(0, 0, 255)', label: '0-4' },
  { min: 4, max: 7, color: 'rgb(0, 127, 255)', label: '4-7' },
  { min: 7, max: 11, color: 'rgb(0, 255, 0)', label: '7-11' },
  { min: 11, max: 16, color: 'rgb(255, 255, 0)', label: '11-16' },
  { min: 16, max: 26, color: 'rgb(255, 170, 0)', label: '16-26' },
  { min: 26, max: null, color: 'rgb(255, 0, 0)', label: '26+' }
]

export const TEMPERATURE_COLOR_BREAKS: ColorBreak[] = [
  { min: -50, max: 0, color: 'rgb(0, 64, 255)', label: '<0 C' },
  { min: 0, max: 10, color: 'rgb(0, 191, 255)', label: '0-10 C' },
  { min: 10, max: 20, color: 'rgb(0, 180, 0)', label: '10-20 C' },
  { min: 20, max: 30, color: 'rgb(255, 214, 0)', label: '20-30 C' },
  { min: 30, max: null, color: 'rgb(220, 0, 0)', label: '30+ C' }
]

export const RH_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 20, color: 'rgb(220, 0, 0)', label: '0-20%' },
  { min: 20, max: 40, color: 'rgb(255, 170, 0)', label: '20-40%' },
  { min: 40, max: 60, color: 'rgb(255, 255, 0)', label: '40-60%' },
  { min: 60, max: 80, color: 'rgb(0, 191, 255)', label: '60-80%' },
  { min: 80, max: null, color: 'rgb(0, 0, 255)', label: '80%+' }
]

export const WIND_SPEED_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 10, color: 'rgb(210, 255, 255)', label: '0-10 km/h' },
  { min: 10, max: 20, color: 'rgb(0, 255, 0)', label: '10-20 km/h' },
  { min: 20, max: 40, color: 'rgb(255, 255, 0)', label: '20-40 km/h' },
  { min: 40, max: 60, color: 'rgb(255, 170, 0)', label: '40-60 km/h' },
  { min: 60, max: null, color: 'rgb(255, 0, 0)', label: '60+ km/h' }
]

export const WIND_DIRECTION_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 45, color: 'rgb(230, 25, 75)', label: 'N-NE' },
  { min: 45, max: 90, color: 'rgb(245, 130, 48)', label: 'NE-E' },
  { min: 90, max: 135, color: 'rgb(255, 225, 25)', label: 'E-SE' },
  { min: 135, max: 180, color: 'rgb(60, 180, 75)', label: 'SE-S' },
  { min: 180, max: 225, color: 'rgb(70, 240, 240)', label: 'S-SW' },
  { min: 225, max: 270, color: 'rgb(0, 130, 200)', label: 'SW-W' },
  { min: 270, max: 315, color: 'rgb(145, 30, 180)', label: 'W-NW' },
  { min: 315, max: null, color: 'rgb(240, 50, 230)', label: 'NW-N' }
]

export const PRECIPITATION_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 0.1, color: 'rgb(245, 245, 245)', label: '<0.1 mm' },
  { min: 0.1, max: 2, color: 'rgb(180, 220, 255)', label: '0.1-2 mm' },
  { min: 2, max: 5, color: 'rgb(80, 170, 255)', label: '2-5 mm' },
  { min: 5, max: 10, color: 'rgb(0, 90, 220)', label: '5-10 mm' },
  { min: 10, max: 20, color: 'rgb(80, 30, 180)', label: '10-20 mm' },
  { min: 20, max: null, color: 'rgb(120, 0, 120)', label: '20+ mm' }
]

// Fuel type color mappings based on BCWS standard colors
export const FUEL_TYPE_COLORS: FuelTypeColorMapping[] = [
  { value: 1, fuelCode: 'C-1', color: 'rgb(209, 255, 115)', rgb: [209, 255, 115] },
  { value: 2, fuelCode: 'C-2', color: 'rgb(34, 102, 51)', rgb: [34, 102, 51] },
  { value: 3, fuelCode: 'C-3', color: 'rgb(131, 199, 149)', rgb: [131, 199, 149] },
  { value: 4, fuelCode: 'C-4', color: 'rgb(112, 168, 0)', rgb: [112, 168, 0] },
  { value: 5, fuelCode: 'C-5', color: 'rgb(223, 184, 230)', rgb: [223, 184, 230] },
  { value: 6, fuelCode: 'C-6', color: 'rgb(172, 102, 237)', rgb: [172, 102, 237] },
  { value: 7, fuelCode: 'C-7', color: 'rgb(112, 12, 242)', rgb: [112, 12, 242] },
  { value: 8, fuelCode: 'D-1/D-2', color: 'rgb(137, 112, 68)', rgb: [137, 112, 68] },
  { value: 9, fuelCode: 'S-1', color: 'rgb(251, 190, 185)', rgb: [251, 190, 185] },
  { value: 10, fuelCode: 'S-2', color: 'rgb(247, 104, 161)', rgb: [247, 104, 161] },
  { value: 11, fuelCode: 'S-3', color: 'rgb(174, 1, 126)', rgb: [174, 1, 126] },
  { value: 12, fuelCode: 'O-1a/O-1b', color: 'rgb(255, 255, 190)', rgb: [255, 255, 190] },
  { value: 13, fuelCode: 'M-3', color: 'rgb(255, 211, 127)', rgb: [255, 211, 127] },
  { value: 14, fuelCode: 'M-1/M-2', color: 'rgb(255, 211, 127)', rgb: [255, 211, 127] }
]

// Convert fuel type colors to color breaks format for consistency with other rasters
export const FUEL_COLOR_BREAKS: ColorBreak[] = FUEL_TYPE_COLORS.map(({ value, fuelCode, color }) => ({
  min: value,
  max: value,
  color,
  label: fuelCode
}))

export const RASTER_CONFIG: Record<RasterType, RasterConfig> = {
  fwi: { label: 'FWI', colorBreaks: FWI_COLOR_BREAKS },
  dmc: { label: 'DMC', colorBreaks: DMC_COLOR_BREAKS },
  dc: { label: 'DC', colorBreaks: DC_COLOR_BREAKS },
  ffmc: { label: 'FFMC', colorBreaks: FFMC_COLOR_BREAKS },
  bui: { label: 'BUI', colorBreaks: BUI_COLOR_BREAKS },
  isi: { label: 'ISI', colorBreaks: ISI_COLOR_BREAKS },
  temperature: { label: 'Temperature', colorBreaks: TEMPERATURE_COLOR_BREAKS },
  relative_humidity: { label: 'Relative Humidity', colorBreaks: RH_COLOR_BREAKS },
  wind_speed: { label: 'Wind Speed', colorBreaks: WIND_SPEED_COLOR_BREAKS },
  wind_direction: { label: 'Wind Direction', colorBreaks: WIND_DIRECTION_COLOR_BREAKS },
  precipitation: { label: 'Precipitation', colorBreaks: PRECIPITATION_COLOR_BREAKS },
  fuel: { label: 'Fuel', colorBreaks: FUEL_COLOR_BREAKS }
}

// Backward compatibility - export just the color breaks
export const RASTER_COLOR_BREAKS: Record<RasterType, ColorBreak[]> = {
  fwi: FWI_COLOR_BREAKS,
  dmc: DMC_COLOR_BREAKS,
  dc: DC_COLOR_BREAKS,
  ffmc: FFMC_COLOR_BREAKS,
  bui: BUI_COLOR_BREAKS,
  isi: ISI_COLOR_BREAKS,
  temperature: TEMPERATURE_COLOR_BREAKS,
  relative_humidity: RH_COLOR_BREAKS,
  wind_speed: WIND_SPEED_COLOR_BREAKS,
  wind_direction: WIND_DIRECTION_COLOR_BREAKS,
  precipitation: PRECIPITATION_COLOR_BREAKS,
  fuel: FUEL_COLOR_BREAKS
}
