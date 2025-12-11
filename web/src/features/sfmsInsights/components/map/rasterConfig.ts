import { FireWeatherRasterType } from './layerDefinitions'

export interface ColorBreak {
  min: number
  max: number | null
  color: string
  label: string
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

export const RASTER_CONFIG: Record<FireWeatherRasterType, RasterConfig> = {
  fwi: { label: 'FWI', colorBreaks: FWI_COLOR_BREAKS },
  dmc: { label: 'DMC', colorBreaks: DMC_COLOR_BREAKS },
  dc: { label: 'DC', colorBreaks: DC_COLOR_BREAKS },
  ffmc: { label: 'FFMC', colorBreaks: FFMC_COLOR_BREAKS },
  bui: { label: 'BUI', colorBreaks: BUI_COLOR_BREAKS },
  isi: { label: 'ISI', colorBreaks: ISI_COLOR_BREAKS }
}

// Backward compatibility - export just the color breaks
export const RASTER_COLOR_BREAKS: Record<FireWeatherRasterType, ColorBreak[]> = {
  fwi: FWI_COLOR_BREAKS,
  dmc: DMC_COLOR_BREAKS,
  dc: DC_COLOR_BREAKS,
  ffmc: FFMC_COLOR_BREAKS,
  bui: BUI_COLOR_BREAKS,
  isi: ISI_COLOR_BREAKS
}
