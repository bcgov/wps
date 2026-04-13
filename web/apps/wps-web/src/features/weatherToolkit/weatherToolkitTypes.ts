export enum ModelType {
  GDPS = 'GDPS',
  RDPS = 'RDPS'
}

export const modelRegistry = {
  [ModelType.GDPS]: {
    ecccPath: 'model_gdps',
    resolution: '15km',
    interval: 6,
    maxHour: 240
  },
  [ModelType.RDPS]: {
    ecccPath: 'model_rdps',
    resolution: '10km',
    interval: 3,
    maxHour: 84
  }
}

export enum ModelRunHour {
  ZERO = '00',
  TWELVE = '12'
}

export const CONTROL_BACKGROUND_COLOUR = '#fcfdfe'
export const BUTTON_BORDER_COLOUR = 'rgba(0,51,102,0.15)'
export const BUTTON_HOVER_BACKGROUND_COLOUR = '#f0f4f8'
export const BORDER_AND_SHADOW_COLOUR = 'rgba(0,0,0,0.1)'
export const BOX_SHADOW_COLOUR = 'rgba(0,0,0,0.05)'
