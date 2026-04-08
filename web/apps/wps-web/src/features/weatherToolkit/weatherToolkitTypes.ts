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
