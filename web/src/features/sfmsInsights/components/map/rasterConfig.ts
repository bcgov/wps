export type FireWeatherRasterType = 'fwi' | 'dmc' | 'dc' | 'ffmc' | 'bui' | 'isi' | 'fuel'

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

export const RASTER_CONFIG: Record<FireWeatherRasterType, RasterConfig> = {
  fwi: { label: 'FWI', colorBreaks: FWI_COLOR_BREAKS },
  dmc: { label: 'DMC', colorBreaks: DMC_COLOR_BREAKS },
  dc: { label: 'DC', colorBreaks: DC_COLOR_BREAKS },
  ffmc: { label: 'FFMC', colorBreaks: FFMC_COLOR_BREAKS },
  bui: { label: 'BUI', colorBreaks: BUI_COLOR_BREAKS },
  isi: { label: 'ISI', colorBreaks: ISI_COLOR_BREAKS },
  fuel: { label: 'Fuel Type', colorBreaks: FUEL_COLOR_BREAKS }
}

// Backward compatibility - export just the color breaks
export const RASTER_COLOR_BREAKS: Record<FireWeatherRasterType, ColorBreak[]> = {
  fwi: FWI_COLOR_BREAKS,
  dmc: DMC_COLOR_BREAKS,
  dc: DC_COLOR_BREAKS,
  ffmc: FFMC_COLOR_BREAKS,
  bui: BUI_COLOR_BREAKS,
  isi: ISI_COLOR_BREAKS,
  fuel: FUEL_COLOR_BREAKS
}
