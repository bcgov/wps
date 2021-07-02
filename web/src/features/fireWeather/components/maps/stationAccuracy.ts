export interface StationMetrics {
  observations: {
    temperature: number
    relative_humidity: number
  } | null
  forecasts: {
    temperature: number
    relative_humidity: number
  } | null
}

export const noDataColor = '#000000'
export const neutralColor = '#DFDEDB'
export const neutralIndex = 3

export const rhColorScale = [
  '#07A059',
  '#3BAC48',
  '#82C064',
  neutralColor,
  '#FCCE89',
  '#F4A036',
  '#ED8001'
]
export const tempColorScale = [
  '#720505',
  '#D05050',
  '#F79191',
  neutralColor,
  '#60D3F8',
  '#38B0F8',
  '#2F80EE'
]

export const windColorScale = [
  '#460270',
  '#BC69EF',
  '#D6B2ED',
  neutralColor,
  '#7AD3CE',
  '#17B8A7',
  '#089E83'
]

export const tempGradientStepInDegrees = 2
export const rhGradientStepInPercentagePoints = 3

export const computeTempAccuracyColor = (stationMetric: StationMetrics): string => {
  if (stationMetric.observations == null || stationMetric.forecasts == null) {
    return noDataColor
  }
  return tempColorScale[computeTempScaleIndex(
    stationMetric.forecasts.temperature,
    stationMetric.observations.temperature
  )]
}

export const computeRHAccuracyColor = (stationMetric: StationMetrics): string => {
  if (stationMetric.observations == null || stationMetric.forecasts == null) {
    return noDataColor
  }
  return rhColorScale[computeRHScaleIndex(
    stationMetric.forecasts.relative_humidity,
    stationMetric.observations.relative_humidity
  )]
}

export const computeRHScaleIndex = (
  metricForecast: number,
  metricObservation: number
): number => {
  const percentagePointDifference = metricObservation - metricForecast
  const gradient = Math.floor(
    percentagePointDifference / rhGradientStepInPercentagePoints
  )
  const scaleIndex = Math.min(gradient + neutralIndex, (rhColorScale.length - 1) / 2)
  return scaleIndex
}

export const computeTempScaleIndex = (
  metricForecast: number,
  metricObservation: number
): number => {
  const tempDifference = metricObservation - metricForecast
  const gradient = Math.floor(tempDifference / tempGradientStepInDegrees)
  const scaleIndex = Math.min(gradient + neutralIndex, (tempColorScale.length - 1) / 2)
  return scaleIndex
}
