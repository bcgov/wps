import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'

export const calculateMeanIntensityGroup = (
  area: PlanningArea,
  dailiesMap: Map<number, StationDaily>,
  selected: number[]
): number | undefined => {
  const stationCodesInPlanningArea: number[] = Object.entries(area.stations).map(
    ([, station]) => station.code
  )
  const stationIntensityGroups: number[] = []
  for (const code of stationCodesInPlanningArea) {
    if (selected.includes(code)) {
      const stationDaily = dailiesMap.get(code)
      if (stationDaily?.intensity_group !== undefined) {
        stationIntensityGroups.push(stationDaily?.intensity_group)
      }
    }
  }
  return stationIntensityGroups.length === 0
    ? undefined
    : Math.ceil(
        (10 * stationIntensityGroups.reduce((a, b) => a + b, 0)) /
          stationIntensityGroups.length /
          10
      )
}
export const intensityGroupColours: { [description: string]: string } = {
  lightGreen: '#D6FCA4',
  cyan: '#73FBFD',
  yellow: '#FFFEA6',
  orange: '#F7CDA0',
  red: '#EC5D57'
}
