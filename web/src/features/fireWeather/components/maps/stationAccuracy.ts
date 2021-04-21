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
    computePercentageDifference(
      stationMetric.forecasts.temperature,
      stationMetric.observations.temperature
    ),
    computePercentageDifference(
      stationMetric.forecasts.relative_humidity,
      stationMetric.observations.relative_humidity
    )
  )
}

export const computePercentageDifference = (
  metricForecast: number,
  metricObservation: number
) => {
  let percentDifference =
    ((metricForecast - metricObservation) / ((metricForecast + metricObservation) / 2)) *
    100
  percentDifference = isNaN(percentDifference) ? 0 : percentDifference

  return percentDifference
}

/**
 *  Return color code for metric percent differences.
 *
 *  Index is determined by how many multiples of 3 the difference
 *  is from the observed result, bounded by the size of the color array.
 */
export const determineColor = (
  tempPercentDifference: number,
  rhPercentDifference: number
): ColorResult => {
  return {
    temperature:
      tempColorScale[
        computeScaleIndex(
          tempPercentDifference,
          differenceToMagnitude(tempPercentDifference),
          tempColorScale
        )
      ],
    relative_humidity:
      rhColorScale[
        computeScaleIndex(
          rhPercentDifference,
          differenceToMagnitude(rhPercentDifference),
          rhColorScale
        )
      ]
  }
}

export const computeScaleIndex = (
  percentDifference: number,
  scaleMagnitude: number,
  scale: string[]
): number => {
  return percentDifference <= 0
    ? Math.max(neutralIndex - scaleMagnitude, 0)
    : Math.min(neutralIndex + scaleMagnitude, scale.length - 1)
}

export const differenceToMagnitude = (percentDifference: number): number => {
  return Math.min(Math.floor(Math.abs(percentDifference) / 3), rhColorScale.length - 1)
}
