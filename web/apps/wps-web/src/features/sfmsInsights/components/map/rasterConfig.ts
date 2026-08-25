export type RasterType =
  | 'fuel'
  | 'fwi'
  | 'dmc'
  | 'dc'
  | 'ffmc'
  | 'bui'
  | 'isi'
  | 'sfc'
  | 'fmc'
  | 'temperature'
  | 'relative_humidity'
  | 'wind_speed'
  | 'wind_direction'
  | 'precipitation'

export type SFMSNGRasterType = Exclude<RasterType, 'fuel'>

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
  tooltipDecimalPlaces?: number
}

const RASTER_COLORS = {
  blue: 'rgb(0, 0, 255)',
  lightBlue: 'rgb(0, 127, 255)',
  blueGrey: 'rgb(102, 153, 204)',
  paleBlue: 'rgb(177, 204, 245)',
  green: 'rgb(0, 255, 0)',
  darkGreen: 'rgb(0, 170, 0)',
  lime: 'rgb(128, 255, 0)',
  yellow: 'rgb(255, 255, 0)',
  orange: 'rgb(255, 170, 0)',
  red: 'rgb(255, 0, 0)',
  magenta: 'rgb(180, 0, 140)'
} as const

export const FWI_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 8, color: RASTER_COLORS.blue, label: '0-8' },
  { min: 8, max: 17, color: RASTER_COLORS.lightBlue, label: '8-17' },
  { min: 17, max: 27, color: RASTER_COLORS.green, label: '17-27' },
  { min: 27, max: 38, color: RASTER_COLORS.yellow, label: '27-38' },
  { min: 38, max: 47, color: RASTER_COLORS.orange, label: '38-47' },
  { min: 47, max: null, color: RASTER_COLORS.red, label: '47+' }
]

export const DMC_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 35, color: RASTER_COLORS.blue, label: '0-35' },
  { min: 35, max: 50, color: RASTER_COLORS.green, label: '35-50' },
  { min: 50, max: 75, color: RASTER_COLORS.yellow, label: '50-75' },
  { min: 75, max: 100, color: RASTER_COLORS.orange, label: '75-100' },
  { min: 100, max: null, color: RASTER_COLORS.red, label: '100+' }
]

export const DC_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 150, color: RASTER_COLORS.blue, label: '0-150' },
  { min: 150, max: 250, color: RASTER_COLORS.lightBlue, label: '150-250' },
  { min: 250, max: 350, color: RASTER_COLORS.green, label: '250-350' },
  { min: 350, max: 500, color: RASTER_COLORS.yellow, label: '350-500' },
  { min: 500, max: 750, color: RASTER_COLORS.orange, label: '500-750' },
  { min: 750, max: null, color: RASTER_COLORS.red, label: '750+' }
]

export const BUI_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 50, color: RASTER_COLORS.blue, label: '0-50' },
  { min: 50, max: 90, color: RASTER_COLORS.lightBlue, label: '50-90' },
  { min: 90, max: 140, color: RASTER_COLORS.green, label: '90-140' },
  { min: 140, max: 160, color: RASTER_COLORS.yellow, label: '140-160' },
  { min: 160, max: 200, color: RASTER_COLORS.orange, label: '160-200' },
  { min: 200, max: null, color: RASTER_COLORS.red, label: '200+' }
]

export const FFMC_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 25, color: 'rgb(210, 255, 255)', label: '0-25' },
  { min: 25, max: 35, color: 'rgb(160, 210, 255)', label: '25-35' },
  { min: 35, max: 45, color: RASTER_COLORS.lightBlue, label: '35-45' },
  { min: 45, max: 55, color: RASTER_COLORS.blue, label: '45-55' },
  { min: 55, max: 65, color: RASTER_COLORS.green, label: '55-65' },
  { min: 65, max: 75, color: 'rgb(0, 127, 0)', label: '65-75' },
  { min: 75, max: 85, color: RASTER_COLORS.yellow, label: '75-85' },
  { min: 85, max: 90, color: RASTER_COLORS.orange, label: '85-90' },
  { min: 90, max: 93, color: RASTER_COLORS.red, label: '90-93' },
  { min: 93, max: 96, color: 'rgb(190, 50, 0)', label: '93-96' },
  { min: 96, max: null, color: 'rgb(127, 0, 0)', label: '96+' }
]

export const ISI_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 4, color: RASTER_COLORS.blue, label: '0-4' },
  { min: 4, max: 7, color: RASTER_COLORS.lightBlue, label: '4-7' },
  { min: 7, max: 11, color: RASTER_COLORS.green, label: '7-11' },
  { min: 11, max: 16, color: RASTER_COLORS.yellow, label: '11-16' },
  { min: 16, max: 26, color: RASTER_COLORS.orange, label: '16-26' },
  { min: 26, max: null, color: RASTER_COLORS.red, label: '26+' }
]

export const SFC_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 1, color: RASTER_COLORS.blue, label: '0-1' },
  { min: 1, max: 2, color: RASTER_COLORS.blueGrey, label: '1-2' },
  { min: 2, max: 3, color: RASTER_COLORS.darkGreen, label: '2-3' },
  { min: 3, max: 4, color: RASTER_COLORS.lime, label: '3-4' },
  { min: 4, max: 5, color: RASTER_COLORS.yellow, label: '4-5' },
  { min: 5, max: 7.6, color: RASTER_COLORS.orange, label: '5-7.6' },
  { min: 7.6, max: null, color: RASTER_COLORS.red, label: '7.6+' }
]

export const FMC_COLOR_BREAKS: ColorBreak[] = [
  { min: Number.NEGATIVE_INFINITY, max: 85, color: RASTER_COLORS.orange, label: '<85' },
  { min: 85, max: 90, color: RASTER_COLORS.yellow, label: '85-90' },
  { min: 90, max: 95, color: RASTER_COLORS.lime, label: '90-95' },
  { min: 95, max: 100, color: RASTER_COLORS.darkGreen, label: '95-100' },
  { min: 100, max: 110, color: RASTER_COLORS.blueGrey, label: '100-110' },
  { min: 110, max: null, color: RASTER_COLORS.blue, label: '110+' }
]

export const TEMPERATURE_COLOR_BREAKS: ColorBreak[] = [
  { min: -50, max: 0, color: RASTER_COLORS.blue, label: '< 0 C' },
  { min: 0, max: 3, color: RASTER_COLORS.blueGrey, label: '0 - 3 C' },
  { min: 3, max: 6, color: RASTER_COLORS.paleBlue, label: '3 - 6 C' },
  { min: 6, max: 11, color: RASTER_COLORS.darkGreen, label: '6 - 11 C' },
  { min: 11, max: 16, color: RASTER_COLORS.lime, label: '11 - 16 C' },
  { min: 16, max: 20, color: RASTER_COLORS.yellow, label: '16 - 20 C' },
  { min: 20, max: 25, color: RASTER_COLORS.orange, label: '20 - 25 C' },
  { min: 25, max: 31, color: RASTER_COLORS.red, label: '25 - 31 C' },
  { min: 31, max: null, color: RASTER_COLORS.magenta, label: '31+ C' }
]

export const RH_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 16, color: RASTER_COLORS.red, label: '0 - 16%' },
  { min: 16, max: 26, color: RASTER_COLORS.orange, label: '16 - 26%' },
  { min: 26, max: 35, color: RASTER_COLORS.yellow, label: '26 - 35%' },
  { min: 35, max: 50, color: RASTER_COLORS.lime, label: '35 - 50%' },
  { min: 50, max: 70, color: RASTER_COLORS.blueGrey, label: '50 - 70%' },
  { min: 70, max: null, color: RASTER_COLORS.blue, label: '70%+' }
]

export const WIND_SPEED_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 4, color: RASTER_COLORS.blue, label: '0 - 4 km/h' },
  { min: 4, max: 9, color: RASTER_COLORS.blueGrey, label: '4 - 9 km/h' },
  { min: 9, max: 13, color: RASTER_COLORS.paleBlue, label: '9 - 13 km/h' },
  { min: 13, max: 17, color: RASTER_COLORS.darkGreen, label: '13 - 17 km/h' },
  { min: 17, max: 21, color: RASTER_COLORS.lime, label: '17 - 21 km/h' },
  { min: 21, max: 25, color: RASTER_COLORS.orange, label: '21 - 25 km/h' },
  { min: 25, max: 31, color: RASTER_COLORS.red, label: '25 - 31 km/h' },
  { min: 31, max: null, color: RASTER_COLORS.magenta, label: '31+ km/h' }
]

export const WIND_DIRECTION_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 45, color: RASTER_COLORS.blue, label: 'North' },
  { min: 45, max: 90, color: RASTER_COLORS.blueGrey, label: 'Northeast' },
  { min: 90, max: 135, color: RASTER_COLORS.paleBlue, label: 'East' },
  { min: 135, max: 180, color: RASTER_COLORS.darkGreen, label: 'Southeast' },
  { min: 180, max: 225, color: RASTER_COLORS.lime, label: 'South' },
  { min: 225, max: 270, color: RASTER_COLORS.yellow, label: 'Southwest' },
  { min: 270, max: 315, color: RASTER_COLORS.orange, label: 'West' },
  { min: 315, max: null, color: RASTER_COLORS.red, label: 'Northwest' }
]

export const PRECIPITATION_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 0.1, color: RASTER_COLORS.red, label: '0.0 - 0.1 mm' },
  { min: 0.1, max: 0.6, color: RASTER_COLORS.orange, label: '0.1 - 0.6 mm' },
  { min: 0.6, max: 1.5, color: RASTER_COLORS.yellow, label: '0.6 - 1.5 mm' },
  { min: 1.5, max: 2.5, color: RASTER_COLORS.lime, label: '1.5 - 2.5 mm' },
  { min: 2.5, max: 5, color: RASTER_COLORS.darkGreen, label: '2.5 - 5.0 mm' },
  { min: 5, max: 10, color: RASTER_COLORS.blueGrey, label: '5 - 10 mm' },
  { min: 10, max: 25, color: RASTER_COLORS.blue, label: '10 - 25 mm' },
  { min: 25, max: null, color: 'rgb(0, 0, 128)', label: '25+ mm' }
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
  fuel: { label: 'Fuel', colorBreaks: FUEL_COLOR_BREAKS },
  fwi: { label: 'FWI', colorBreaks: FWI_COLOR_BREAKS },
  dmc: { label: 'DMC', colorBreaks: DMC_COLOR_BREAKS },
  dc: { label: 'DC', colorBreaks: DC_COLOR_BREAKS },
  ffmc: { label: 'FFMC', colorBreaks: FFMC_COLOR_BREAKS },
  bui: { label: 'BUI', colorBreaks: BUI_COLOR_BREAKS },
  isi: { label: 'ISI', colorBreaks: ISI_COLOR_BREAKS },
  sfc: { label: 'SFC', colorBreaks: SFC_COLOR_BREAKS, tooltipDecimalPlaces: 1 },
  fmc: { label: 'FMC', colorBreaks: FMC_COLOR_BREAKS },
  temperature: { label: 'Temperature', colorBreaks: TEMPERATURE_COLOR_BREAKS },
  relative_humidity: { label: 'Relative Humidity', colorBreaks: RH_COLOR_BREAKS },
  wind_speed: { label: 'Wind Speed', colorBreaks: WIND_SPEED_COLOR_BREAKS },
  wind_direction: { label: 'Wind Direction', colorBreaks: WIND_DIRECTION_COLOR_BREAKS },
  precipitation: { label: 'Precipitation', colorBreaks: PRECIPITATION_COLOR_BREAKS }
}

// Backward compatibility - export just the color breaks
export const RASTER_COLOR_BREAKS: Record<RasterType, ColorBreak[]> = {
  fwi: FWI_COLOR_BREAKS,
  dmc: DMC_COLOR_BREAKS,
  dc: DC_COLOR_BREAKS,
  ffmc: FFMC_COLOR_BREAKS,
  bui: BUI_COLOR_BREAKS,
  isi: ISI_COLOR_BREAKS,
  sfc: SFC_COLOR_BREAKS,
  fmc: FMC_COLOR_BREAKS,
  temperature: TEMPERATURE_COLOR_BREAKS,
  relative_humidity: RH_COLOR_BREAKS,
  wind_speed: WIND_SPEED_COLOR_BREAKS,
  wind_direction: WIND_DIRECTION_COLOR_BREAKS,
  precipitation: PRECIPITATION_COLOR_BREAKS,
  fuel: FUEL_COLOR_BREAKS
}
