export interface StationMetrics {
  observations: {
    temperature: number
    relative_humidity: number
  }
  forecasts: {
    temperature: number
    relative_humidity: number
  }
}

export interface ColorResult {
  temperature: string
  relative_humidity: string
}

export const neutralColor = '#DFDEDB'
const neutralIndex = 3

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
    return { temperature: '#000000', relative_humidity: '#000000' }
  }
  const tempPercentDifference =
    ((stationMetric.forecasts.temperature - stationMetric.observations.temperature) /
      stationMetric.observations.temperature) *
    100

  const rhPercentDifference =
    ((stationMetric.forecasts.relative_humidity -
      stationMetric.observations.relative_humidity) /
      stationMetric.observations.relative_humidity) *
    100

  return determineColor(tempPercentDifference, rhPercentDifference)
}

/**
 *  Return color code for metric percent differences.
 *
 *  Index is determined by how many multiples of 3 the difference
 *  is from the observed result, bounded by the size of the color array.
 */
const determineColor = (
  tempPercentDifference: number,
  rhPercentDifference: number
): ColorResult => {
  const tempScaleMagnitude = differenceToMagnitude(tempPercentDifference)

  const rhScaleMagnitude = differenceToMagnitude(rhPercentDifference)

  const tempScaleIndex =
    tempPercentDifference < 0
      ? Math.max(neutralIndex - tempScaleMagnitude, 0)
      : tempScaleMagnitude

  const rhScaleIndex =
    rhPercentDifference < 0
      ? Math.max(neutralIndex - rhScaleMagnitude, 0)
      : rhScaleMagnitude

  return {
    temperature: tempColorScale[tempScaleIndex],
    relative_humidity: rhColorScale[rhScaleIndex]
  }
}

const differenceToMagnitude = (percentDifference: number): number => {
  return isNaN(percentDifference) || Math.abs(percentDifference) < 3
    ? neutralIndex
    : Math.min(Math.floor(Math.abs(percentDifference) / 3), rhColorScale.length - 1)
}
