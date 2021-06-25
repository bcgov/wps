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

export interface ColorResult {
  temperature: string
  relative_humidity: string
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

/**
 *  Calculates the percentage difference between observed and forecasted station metrics.
 *  Uses increments of 3% to determine color code in the associated color arrays.
 *
 * @param stationMetrics contains forecasted and observered temperature and relative humidity
 * @returns color code to display for temperature and relative humidity on the map
 */
export const computeAccuracyColors = (stationMetric: StationMetrics): ColorResult => {
  if (stationMetric.observations == null || stationMetric.forecasts == null) {
    return { temperature: noDataColor, relative_humidity: noDataColor }
  }

  return determineColor(
    computeTempScaleIndex(
      stationMetric.forecasts.temperature,
      stationMetric.observations.temperature
    ),
    computeRHScaleIndex(
      stationMetric.forecasts.relative_humidity,
      stationMetric.observations.relative_humidity
    )
  )
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

/**
 *  Return color code for metric percent differences.
 *
 *  Index is determined by the magnitude of the difference between observed
 *  and forecasted, bounded by the size of the color array.
 */
export const determineColor = (
  tempScaleIndex: number,
  rhScaleIndex: number
): ColorResult => {
  return {
    temperature: tempColorScale[tempScaleIndex],
    relative_humidity: rhColorScale[rhScaleIndex]
  }
}
