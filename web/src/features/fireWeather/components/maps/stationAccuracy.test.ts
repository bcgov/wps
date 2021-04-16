import { computeAccuracyColors, StationMetrics } from './stationAccuracy'

const exactForecast: StationMetrics = {
  observations: {
    temperature: 0,
    relative_humidity: 0
  },
  forecasts: {
    temperature: 0,
    relative_humidity: 0
  }
}
describe('Date util functions', () => {
  it('should return the correct color codes', () => {
    expect(computeAccuracyColors(exactForecast)).toEqual([
      { temperature: neutralColor, relative_humidity: neutralColor }
    ])
  })
})
