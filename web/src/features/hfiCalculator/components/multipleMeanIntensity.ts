import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'

export const calculateMultipleMeanIntensityGroups = (
  area: PlanningArea,
  weekliesMap: Map<number, StationDaily[]>,
  selected: number[]
): number | undefined => {
  const stationCodesInPlanningArea: number[] = Object.entries(area.stations).map(
    ([, station]) => station.code
  )
  const stationIntensityGroups: number[] = []
  for (const code of stationCodesInPlanningArea) {
    if (selected.includes(code)) {
      const dailies = weekliesMap.get(code)
      if (dailies) {
        for (let i = 0; i < dailies.length; i++) {
          if (dailies[i].intensity_group !== undefined) {
            stationIntensityGroups.push(dailies[0].intensity_group)
          }
        }
      }
    }
  }
  return stationIntensityGroups.length === 0
    ? undefined
    : Math.round(
        (10 * stationIntensityGroups.reduce((a, b) => a + b, 0)) /
          stationIntensityGroups.length
      ) / 10
}
export const intensityGroupColours: { [description: string]: string } = {
  lightGreen: '#D6FCA4',
  cyan: '#73FBFD',
  yellow: '#FFFEA6',
  orange: '#F7CDA0',
  red: '#EC5D57'
}
