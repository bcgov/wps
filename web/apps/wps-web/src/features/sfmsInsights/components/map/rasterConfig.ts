export type RasterType =
  | 'fuel'
  | 'fwi'
  | 'dmc'
  | 'dc'
  | 'ffmc'
  | 'bui'
  | 'isi'
  | 'sfc'
  | 'tfc'
  | 'cfb'
  | 'hfi'
  | 'fmc'
  | 'ros'
  | 'temperature'
  | 'relative_humidity'
  | 'wind_speed'
  | 'wind_direction'
  | 'precipitation'

export type SFMSNGRasterType = Exclude<RasterType, 'fuel'>

export interface ColourBreak {
  min: number
  max: number | null
  colour: string
  label: string
}

export interface FuelTypeColourMapping {
  value: number
  fuelCode: string
  rgb: [number, number, number]
}

export type RasterGroup = 'weather' | 'fuel' | 'fwi' | 'fbp'

export interface RasterConfig {
  group: RasterGroup
  label: string
  colourBreaks: ColourBreak[]
  tooltipDecimalPlaces?: number
}

const RASTER_COLOURS = {
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
  magenta: 'rgb(180, 0, 140)',
  fireBehaviourBlue: 'rgb(0, 0, 245)',
  fireBehaviourBlueGrey: 'rgb(113, 152, 201)',
  fireBehaviourGreen: 'rgb(76, 168, 48)',
  fireBehaviourLime: 'rgb(175, 253, 79)',
  fireBehaviourYellow: 'rgb(255, 255, 85)',
  fireBehaviourOrange: 'rgb(243, 174, 61)',
  fireBehaviourRed: 'rgb(234, 51, 35)',
  hfiLightBlue: 'rgb(0, 116, 255)',
  hfiDarkGreen: 'rgb(0, 116, 0)',
  hfiOrange: 'rgb(255, 160, 0)'
} as const

export const FWI_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 8, colour: RASTER_COLOURS.blue, label: '0-8' },
  { min: 8, max: 17, colour: RASTER_COLOURS.lightBlue, label: '8-17' },
  { min: 17, max: 27, colour: RASTER_COLOURS.green, label: '17-27' },
  { min: 27, max: 38, colour: RASTER_COLOURS.yellow, label: '27-38' },
  { min: 38, max: 47, colour: RASTER_COLOURS.orange, label: '38-47' },
  { min: 47, max: null, colour: RASTER_COLOURS.red, label: '47+' }
]

export const DMC_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 35, colour: RASTER_COLOURS.blue, label: '0-35' },
  { min: 35, max: 50, colour: RASTER_COLOURS.green, label: '35-50' },
  { min: 50, max: 75, colour: RASTER_COLOURS.yellow, label: '50-75' },
  { min: 75, max: 100, colour: RASTER_COLOURS.orange, label: '75-100' },
  { min: 100, max: null, colour: RASTER_COLOURS.red, label: '100+' }
]

export const DC_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 150, colour: RASTER_COLOURS.blue, label: '0-150' },
  { min: 150, max: 250, colour: RASTER_COLOURS.lightBlue, label: '150-250' },
  { min: 250, max: 350, colour: RASTER_COLOURS.green, label: '250-350' },
  { min: 350, max: 500, colour: RASTER_COLOURS.yellow, label: '350-500' },
  { min: 500, max: 750, colour: RASTER_COLOURS.orange, label: '500-750' },
  { min: 750, max: null, colour: RASTER_COLOURS.red, label: '750+' }
]

export const BUI_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 50, colour: RASTER_COLOURS.blue, label: '0-50' },
  { min: 50, max: 90, colour: RASTER_COLOURS.lightBlue, label: '50-90' },
  { min: 90, max: 140, colour: RASTER_COLOURS.green, label: '90-140' },
  { min: 140, max: 160, colour: RASTER_COLOURS.yellow, label: '140-160' },
  { min: 160, max: 200, colour: RASTER_COLOURS.orange, label: '160-200' },
  { min: 200, max: null, colour: RASTER_COLOURS.red, label: '200+' }
]

export const FFMC_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 25, colour: 'rgb(210, 255, 255)', label: '0-25' },
  { min: 25, max: 35, colour: 'rgb(160, 210, 255)', label: '25-35' },
  { min: 35, max: 45, colour: RASTER_COLOURS.lightBlue, label: '35-45' },
  { min: 45, max: 55, colour: RASTER_COLOURS.blue, label: '45-55' },
  { min: 55, max: 65, colour: RASTER_COLOURS.green, label: '55-65' },
  { min: 65, max: 75, colour: 'rgb(0, 127, 0)', label: '65-75' },
  { min: 75, max: 85, colour: RASTER_COLOURS.yellow, label: '75-85' },
  { min: 85, max: 90, colour: RASTER_COLOURS.orange, label: '85-90' },
  { min: 90, max: 93, colour: RASTER_COLOURS.red, label: '90-93' },
  { min: 93, max: 96, colour: 'rgb(190, 50, 0)', label: '93-96' },
  { min: 96, max: null, colour: 'rgb(127, 0, 0)', label: '96+' }
]

export const ISI_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 4, colour: RASTER_COLOURS.blue, label: '0-4' },
  { min: 4, max: 7, colour: RASTER_COLOURS.lightBlue, label: '4-7' },
  { min: 7, max: 11, colour: RASTER_COLOURS.green, label: '7-11' },
  { min: 11, max: 16, colour: RASTER_COLOURS.yellow, label: '11-16' },
  { min: 16, max: 26, colour: RASTER_COLOURS.orange, label: '16-26' },
  { min: 26, max: null, colour: RASTER_COLOURS.red, label: '26+' }
]

export const SFC_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 1, colour: RASTER_COLOURS.blue, label: '0-1' },
  { min: 1, max: 2, colour: RASTER_COLOURS.blueGrey, label: '1-2' },
  { min: 2, max: 3, colour: RASTER_COLOURS.darkGreen, label: '2-3' },
  { min: 3, max: 4, colour: RASTER_COLOURS.lime, label: '3-4' },
  { min: 4, max: 5, colour: RASTER_COLOURS.yellow, label: '4-5' },
  { min: 5, max: 7.6, colour: RASTER_COLOURS.orange, label: '5-7.6' },
  { min: 7.6, max: null, colour: RASTER_COLOURS.red, label: '7.6+' }
]

export const TFC_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 2, colour: RASTER_COLOURS.fireBehaviourBlue, label: '0-2' },
  { min: 2, max: 4, colour: RASTER_COLOURS.fireBehaviourBlueGrey, label: '2-4' },
  { min: 4, max: 6, colour: RASTER_COLOURS.fireBehaviourGreen, label: '4-6' },
  { min: 6, max: 8, colour: RASTER_COLOURS.fireBehaviourLime, label: '6-8' },
  { min: 8, max: 10, colour: RASTER_COLOURS.fireBehaviourYellow, label: '8-10' },
  { min: 10, max: 15, colour: RASTER_COLOURS.fireBehaviourOrange, label: '10-15' },
  { min: 15, max: null, colour: RASTER_COLOURS.fireBehaviourRed, label: '15+' }
]

export const CFB_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 0.1, colour: RASTER_COLOURS.fireBehaviourBlue, label: '0-10%' },
  { min: 0.1, max: 0.3, colour: RASTER_COLOURS.fireBehaviourBlueGrey, label: '10-30%' },
  { min: 0.3, max: 0.5, colour: RASTER_COLOURS.fireBehaviourGreen, label: '30-50%' },
  { min: 0.5, max: 0.6, colour: RASTER_COLOURS.fireBehaviourLime, label: '50-60%' },
  { min: 0.6, max: 0.8, colour: RASTER_COLOURS.fireBehaviourYellow, label: '60-80%' },
  { min: 0.8, max: 0.9, colour: RASTER_COLOURS.fireBehaviourOrange, label: '80-90%' },
  { min: 0.9, max: null, colour: RASTER_COLOURS.fireBehaviourRed, label: '90-100%' }
]

export const HFI_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 10, colour: RASTER_COLOURS.blue, label: '0-10' },
  { min: 10, max: 500, colour: RASTER_COLOURS.hfiLightBlue, label: '10-500' },
  { min: 500, max: 2000, colour: RASTER_COLOURS.hfiDarkGreen, label: '500-2,000' },
  { min: 2000, max: 4000, colour: RASTER_COLOURS.green, label: '2,000-4,000' },
  { min: 4000, max: 10000, colour: RASTER_COLOURS.yellow, label: '4,000-10,000' },
  { min: 10000, max: 30000, colour: RASTER_COLOURS.hfiOrange, label: '10,000-30,000' },
  { min: 30000, max: null, colour: RASTER_COLOURS.red, label: '30,000+' }
]

export const ROS_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 1, colour: RASTER_COLOURS.blue, label: '0-1 m/min' },
  { min: 1, max: 3, colour: RASTER_COLOURS.lightBlue, label: '1-3 m/min' },
  { min: 3, max: 10, colour: RASTER_COLOURS.darkGreen, label: '3-10 m/min' },
  { min: 10, max: 18, colour: RASTER_COLOURS.green, label: '10-18 m/min' },
  { min: 18, max: 25, colour: RASTER_COLOURS.lime, label: '18-25 m/min' },
  { min: 25, max: 50, colour: RASTER_COLOURS.orange, label: '25-50 m/min' },
  { min: 50, max: null, colour: RASTER_COLOURS.red, label: '50+ m/min' }
]

export const FMC_COLOUR_BREAKS: ColourBreak[] = [
  { min: Number.NEGATIVE_INFINITY, max: 85, colour: RASTER_COLOURS.orange, label: '<85' },
  { min: 85, max: 90, colour: RASTER_COLOURS.yellow, label: '85-90' },
  { min: 90, max: 95, colour: RASTER_COLOURS.lime, label: '90-95' },
  { min: 95, max: 100, colour: RASTER_COLOURS.darkGreen, label: '95-100' },
  { min: 100, max: 110, colour: RASTER_COLOURS.blueGrey, label: '100-110' },
  { min: 110, max: null, colour: RASTER_COLOURS.blue, label: '110+' }
]

export const TEMPERATURE_COLOUR_BREAKS: ColourBreak[] = [
  { min: -50, max: 0, colour: RASTER_COLOURS.blue, label: '< 0 C' },
  { min: 0, max: 3, colour: RASTER_COLOURS.blueGrey, label: '0 - 3 C' },
  { min: 3, max: 6, colour: RASTER_COLOURS.paleBlue, label: '3 - 6 C' },
  { min: 6, max: 11, colour: RASTER_COLOURS.darkGreen, label: '6 - 11 C' },
  { min: 11, max: 16, colour: RASTER_COLOURS.lime, label: '11 - 16 C' },
  { min: 16, max: 20, colour: RASTER_COLOURS.yellow, label: '16 - 20 C' },
  { min: 20, max: 25, colour: RASTER_COLOURS.orange, label: '20 - 25 C' },
  { min: 25, max: 31, colour: RASTER_COLOURS.red, label: '25 - 31 C' },
  { min: 31, max: null, colour: RASTER_COLOURS.magenta, label: '31+ C' }
]

export const RH_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 16, colour: RASTER_COLOURS.red, label: '0 - 16%' },
  { min: 16, max: 26, colour: RASTER_COLOURS.orange, label: '16 - 26%' },
  { min: 26, max: 35, colour: RASTER_COLOURS.yellow, label: '26 - 35%' },
  { min: 35, max: 50, colour: RASTER_COLOURS.lime, label: '35 - 50%' },
  { min: 50, max: 70, colour: RASTER_COLOURS.blueGrey, label: '50 - 70%' },
  { min: 70, max: null, colour: RASTER_COLOURS.blue, label: '70%+' }
]

export const WIND_SPEED_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 4, colour: RASTER_COLOURS.blue, label: '0 - 4 km/h' },
  { min: 4, max: 9, colour: RASTER_COLOURS.blueGrey, label: '4 - 9 km/h' },
  { min: 9, max: 13, colour: RASTER_COLOURS.paleBlue, label: '9 - 13 km/h' },
  { min: 13, max: 17, colour: RASTER_COLOURS.darkGreen, label: '13 - 17 km/h' },
  { min: 17, max: 21, colour: RASTER_COLOURS.lime, label: '17 - 21 km/h' },
  { min: 21, max: 25, colour: RASTER_COLOURS.orange, label: '21 - 25 km/h' },
  { min: 25, max: 31, colour: RASTER_COLOURS.red, label: '25 - 31 km/h' },
  { min: 31, max: null, colour: RASTER_COLOURS.magenta, label: '31+ km/h' }
]

export const WIND_DIRECTION_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 45, colour: RASTER_COLOURS.blue, label: 'North' },
  { min: 45, max: 90, colour: RASTER_COLOURS.blueGrey, label: 'Northeast' },
  { min: 90, max: 135, colour: RASTER_COLOURS.paleBlue, label: 'East' },
  { min: 135, max: 180, colour: RASTER_COLOURS.darkGreen, label: 'Southeast' },
  { min: 180, max: 225, colour: RASTER_COLOURS.lime, label: 'South' },
  { min: 225, max: 270, colour: RASTER_COLOURS.yellow, label: 'Southwest' },
  { min: 270, max: 315, colour: RASTER_COLOURS.orange, label: 'West' },
  { min: 315, max: null, colour: RASTER_COLOURS.red, label: 'Northwest' }
]

export const PRECIPITATION_COLOUR_BREAKS: ColourBreak[] = [
  { min: 0, max: 0.1, colour: RASTER_COLOURS.red, label: '0.0 - 0.1 mm' },
  { min: 0.1, max: 0.6, colour: RASTER_COLOURS.orange, label: '0.1 - 0.6 mm' },
  { min: 0.6, max: 1.5, colour: RASTER_COLOURS.yellow, label: '0.6 - 1.5 mm' },
  { min: 1.5, max: 2.5, colour: RASTER_COLOURS.lime, label: '1.5 - 2.5 mm' },
  { min: 2.5, max: 5, colour: RASTER_COLOURS.darkGreen, label: '2.5 - 5.0 mm' },
  { min: 5, max: 10, colour: RASTER_COLOURS.blueGrey, label: '5 - 10 mm' },
  { min: 10, max: 25, colour: RASTER_COLOURS.blue, label: '10 - 25 mm' },
  { min: 25, max: null, colour: 'rgb(0, 0, 128)', label: '25+ mm' }
]

// Fuel type color mappings based on BCWS standard colors
export const FUEL_TYPE_COLOURS: FuelTypeColourMapping[] = [
  { value: 1, fuelCode: 'C-1', rgb: [209, 255, 115] },
  { value: 2, fuelCode: 'C-2', rgb: [34, 102, 51] },
  { value: 3, fuelCode: 'C-3', rgb: [131, 199, 149] },
  { value: 4, fuelCode: 'C-4', rgb: [112, 168, 0] },
  { value: 5, fuelCode: 'C-5', rgb: [223, 184, 230] },
  { value: 6, fuelCode: 'C-6', rgb: [172, 102, 237] },
  { value: 7, fuelCode: 'C-7', rgb: [112, 12, 242] },
  { value: 8, fuelCode: 'D-1/D-2', rgb: [137, 112, 68] },
  { value: 9, fuelCode: 'S-1', rgb: [251, 190, 185] },
  { value: 10, fuelCode: 'S-2', rgb: [247, 104, 161] },
  { value: 11, fuelCode: 'S-3', rgb: [174, 1, 126] },
  { value: 12, fuelCode: 'O-1a/O-1b', rgb: [255, 255, 190] },
  { value: 13, fuelCode: 'M-3', rgb: [255, 211, 127] },
  { value: 14, fuelCode: 'M-1/M-2', rgb: [255, 211, 127] },
  { value: 99, fuelCode: 'Non-fuel', rgb: [130, 130, 130] },
  { value: 102, fuelCode: 'Water', rgb: [115, 223, 255] }
]

// Convert fuel type colors to color breaks format for consistency with other rasters
export const FUEL_COLOUR_BREAKS: ColourBreak[] = FUEL_TYPE_COLOURS.map(({ value, fuelCode, rgb }) => ({
  min: value,
  max: value,
  colour: `rgb(${rgb.join(', ')})`,
  label: fuelCode
}))

export const RASTER_CONFIG: Record<RasterType, RasterConfig> = {
  fuel: { group: 'fuel', label: 'Fuel', colourBreaks: FUEL_COLOUR_BREAKS },
  temperature: { group: 'weather', label: 'Temperature', colourBreaks: TEMPERATURE_COLOUR_BREAKS },
  relative_humidity: { group: 'weather', label: 'Relative Humidity', colourBreaks: RH_COLOUR_BREAKS },
  wind_speed: { group: 'weather', label: 'Wind Speed', colourBreaks: WIND_SPEED_COLOUR_BREAKS },
  wind_direction: { group: 'weather', label: 'Wind Direction', colourBreaks: WIND_DIRECTION_COLOUR_BREAKS },
  precipitation: { group: 'weather', label: 'Precipitation', colourBreaks: PRECIPITATION_COLOUR_BREAKS },
  ffmc: { group: 'fwi', label: 'FFMC', colourBreaks: FFMC_COLOUR_BREAKS },
  dmc: { group: 'fwi', label: 'DMC', colourBreaks: DMC_COLOUR_BREAKS },
  dc: { group: 'fwi', label: 'DC', colourBreaks: DC_COLOUR_BREAKS },
  isi: { group: 'fwi', label: 'ISI', colourBreaks: ISI_COLOUR_BREAKS },
  bui: { group: 'fwi', label: 'BUI', colourBreaks: BUI_COLOUR_BREAKS },
  fwi: { group: 'fwi', label: 'FWI', colourBreaks: FWI_COLOUR_BREAKS },
  fmc: { group: 'fbp', label: 'FMC', colourBreaks: FMC_COLOUR_BREAKS },
  sfc: { group: 'fbp', label: 'SFC', colourBreaks: SFC_COLOUR_BREAKS, tooltipDecimalPlaces: 1 },
  ros: { group: 'fbp', label: 'ROS', colourBreaks: ROS_COLOUR_BREAKS, tooltipDecimalPlaces: 1 },
  cfb: { group: 'fbp', label: 'CFB', colourBreaks: CFB_COLOUR_BREAKS },
  tfc: { group: 'fbp', label: 'TFC', colourBreaks: TFC_COLOUR_BREAKS, tooltipDecimalPlaces: 1 },
  hfi: { group: 'fbp', label: 'HFI', colourBreaks: HFI_COLOUR_BREAKS }
}
