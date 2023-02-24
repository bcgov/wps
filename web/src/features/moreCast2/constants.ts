export interface WeatherModel {
  name: string
  range: number
}

export enum WeatherModelEnum {
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  RDPS = 'RDPS',
  MANUAL = 'MANUAL'
}

export const WeatherModels = [
  { name: WeatherModelEnum.GDPS, range: 10 },
  { name: WeatherModelEnum.GFS, range: 10 },
  { name: WeatherModelEnum.HRDPS, range: 2 },
  { name: WeatherModelEnum.RDPS, range: 3.5 },
  { name: WeatherModelEnum.MANUAL, range: 10 }
]
