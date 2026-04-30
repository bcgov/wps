import { isNull } from 'lodash'
import Stroke from 'ol/style/Stroke'

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
export const darkGreenColor = '#005716'
export const middleGreenColor = '#2E8540'
export const lightGreenColor = '#61B56C'
export const neutralColor = '#DFDEDB'
export const yellowColor = '#FFC464'
export const middleOrangeColor = '#FF9334'
export const darkOrangeColor = '#C66400'

export const darkRedColor = '#720505'
export const mediumRedColor = '#D05050'
export const pinkColor = '#F79191'
export const lightBlueColor = '#60D3F8'
export const mediumBlueColor = '#38B0F8'
export const darkBlueColor = '#2F80EE'

export const neutralIndex = 3

export const rhColorScale = [
  darkGreenColor,
  middleGreenColor,
  lightGreenColor,
  neutralColor,
  yellowColor,
  middleOrangeColor,
  darkOrangeColor
]
export const tempColorScale = [
  darkRedColor,
  mediumRedColor,
  pinkColor,
  neutralColor,
  lightBlueColor,
  mediumBlueColor,
  darkBlueColor
]

export const windColorScale = ['#460270', '#BC69EF', '#D6B2ED', neutralColor, '#7AD3CE', '#17B8A7', '#089E83']

export const smallRadius = 4
export const mediumRadius = 5
export const largeRadius = 6
export const xlargeRadius = 7

export const tempGradientStepInDegrees = 2
export const rhGradientStepInPercentagePoints = 3

export const computeTempAccuracyColor = (stationMetric: StationMetrics): string => {
  if (stationMetric.observations == null || stationMetric.forecasts == null) {
    return noDataColor
  }
  return tempColorScale[
    computeTempScaleIndex(stationMetric.forecasts.temperature, stationMetric.observations.temperature)
  ]
}

export const computeRHAccuracyColor = (stationMetric: StationMetrics): string => {
  if (stationMetric.observations == null || stationMetric.forecasts == null) {
    return noDataColor
  }
  return rhColorScale[
    computeRHScaleIndex(stationMetric.forecasts.relative_humidity, stationMetric.observations.relative_humidity)
  ]
}

export const computeRHAccuracySize = (stationMetric: StationMetrics): number => {
  if (isNull(stationMetric.observations) || isNull(stationMetric.forecasts)) {
    return smallRadius
  }
  const rhScaleIndex = computeRHScaleIndex(
    stationMetric.forecasts.relative_humidity,
    stationMetric.observations.relative_humidity
  )
  return determineMarkerRadius(rhScaleIndex)
}

export const computeTempAccuracySize = (stationMetric: StationMetrics): number => {
  if (isNull(stationMetric.observations) || isNull(stationMetric.forecasts)) {
    return smallRadius
  }
  const tempScaleIndex = computeTempScaleIndex(
    stationMetric.forecasts.temperature,
    stationMetric.observations.temperature
  )
  return determineMarkerRadius(tempScaleIndex)
}

export const computeStroke = (markerColor: string): Stroke | undefined => {
  if (markerColor === neutralColor) {
    return new Stroke({ color: 'black', width: 1 })
  }
  return undefined
}

export const determineMarkerRadius = (scaleIndex: number): number => {
  switch (scaleIndex) {
    case 0:
    case 6:
      return xlargeRadius
    case 1:
    case 5:
      return largeRadius
    case 2:
    case 4:
      return mediumRadius
    case 3:
    default:
      return smallRadius
  }
}

export const computeRHScaleIndex = (metricForecast: number, metricObservation: number): number => {
  const percentagePointDifference = metricForecast - metricObservation
  let scaledDifference = percentagePointDifference / rhGradientStepInPercentagePoints
  if (scaledDifference > 0) {
    scaledDifference = Math.ceil(scaledDifference)
  } else if (scaledDifference < 0) {
    scaledDifference = Math.floor(scaledDifference)
  }
  // adjust from 1-indexing of scaledDifference to 0-indexing for rhColorScale
  if (scaledDifference > 0) {
    scaledDifference -= 1
  } else if (scaledDifference < 0) {
    scaledDifference += 1
  }
  const scaledIndex = scaledDifference + neutralIndex
  if (scaledIndex < 0) {
    return 0
  } else {
    return Math.min(scaledIndex, rhColorScale.length - 1)
  }
}

export const computeTempScaleIndex = (metricForecast: number, metricObservation: number): number => {
  const tempDifference = metricForecast - metricObservation
  let scaledDifference = tempDifference / tempGradientStepInDegrees
  if (scaledDifference > 0) {
    scaledDifference = Math.ceil(scaledDifference)
  } else if (scaledDifference < 0) {
    scaledDifference = Math.floor(scaledDifference)
  }
  // adjust from 1-indexing of scaledDifference to 0-indexing for tempColorScale
  if (scaledDifference > 0) {
    scaledDifference -= 1
  } else if (scaledDifference < 0) {
    scaledDifference += 1
  }
  const scaledIndex = scaledDifference + neutralIndex
  if (scaledIndex < 0) {
    return 0
  } else {
    return Math.min(scaledIndex, tempColorScale.length - 1)
  }
}
