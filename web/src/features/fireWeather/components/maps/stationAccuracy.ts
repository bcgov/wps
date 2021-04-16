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

const rhColorScale = [
  '#07A059',
  '#3BAC48',
  '#82C064',
  '#DFDEDB',
  '#FCCE89',
  '#F4A036',
  '#ED8001'
]
const tempColorScale = [
  '#720505',
  '#D05050',
  '#F79191',
  '#DFDEDB',
  '#60D3F8',
  '#38B0F8',
  '#2F80EE'
]

const windColorScale = [
  '#460270',
  '#BC69EF',
  '#D6B2ED',
  '#DFDEDB',
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
export const computeAccuracyColors = (
  stationMetrics: StationMetrics[]
): ColorResult[] => {
  return stationMetrics.map(stationMetric => {
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
  })
}

const determineColor = (
  tempPercentDifference: number,
  rhPercentDifference: number
): ColorResult => {
  const tempScaleIndex = Math.floor(tempPercentDifference / 3)
  const rhScaleIndex = Math.floor(rhPercentDifference / 3)

  // TODO ...
  return { temperature: '#fffff', relative_humidity: '#fffff' }
}
