import {
  computeAccuracyColors,
  StationMetrics,
  neutralColor,
  noDataColor,
  tempColorScale,
  rhColorScale,
  computePercentageDifference,
  computeScaleIndex,
  neutralIndex
} from './stationAccuracy'

describe('Station map color accuracy', () => {
  describe('computeAccuracyColors', () => {
    it('should return the neutral color code when observed an forecasted are equal', () => {
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
      expect(computeAccuracyColors(exactForecast)).toEqual({
        temperature: neutralColor,
        relative_humidity: neutralColor
      })
    })

    it('should return the no data color code when observed or forecasted is null', () => {
      const nullForecast: StationMetrics = {
        observations: null,
        forecasts: null
      }
      expect(computeAccuracyColors(nullForecast)).toEqual({
        temperature: noDataColor,
        relative_humidity: noDataColor
      })
    })

    it('should return the coolest color when metrics are widely over forecasted', () => {
      const largeDifference: StationMetrics = {
        observations: {
          temperature: 0,
          relative_humidity: 0
        },
        forecasts: {
          temperature: 300,
          relative_humidity: 300
        }
      }
      expect(computeAccuracyColors(largeDifference)).toEqual({
        temperature: tempColorScale[tempColorScale.length - 1],
        relative_humidity: rhColorScale[rhColorScale.length - 1]
      })
    })
    it('should return the warmest color when metrics are widely under forecasted', () => {
      const largeDifference: StationMetrics = {
        observations: {
          temperature: 300,
          relative_humidity: 300
        },
        forecasts: {
          temperature: 0,
          relative_humidity: 0
        }
      }
      expect(computeAccuracyColors(largeDifference)).toEqual({
        temperature: tempColorScale[0],
        relative_humidity: rhColorScale[0]
      })
    })
    it('should return a warmer color when metrics are under forecasted', () => {
      const underForecasted: StationMetrics = {
        observations: {
          temperature: 9,
          relative_humidity: 9
        },
        forecasts: {
          temperature: 8.3,
          relative_humidity: 8.3
        }
      }
      expect(computeAccuracyColors(underForecasted)).toEqual({
        temperature: tempColorScale[1],
        relative_humidity: rhColorScale[1]
      })
    })

    it('should return a cooler color when metrics are over forecasted', () => {
      const overForecasted: StationMetrics = {
        observations: {
          temperature: 8.3,
          relative_humidity: 8.3
        },
        forecasts: {
          temperature: 9,
          relative_humidity: 9
        }
      }
      expect(computeAccuracyColors(overForecasted)).toEqual({
        temperature: tempColorScale[5],
        relative_humidity: rhColorScale[5]
      })
    })
  })
  describe('computePercentageDifference', () => {
    it('computes 100% as difference', () => {
      expect(computePercentageDifference(3, 1)).toEqual(100)
    })
    it('computes 0% as difference', () => {
      expect(computePercentageDifference(0, 0)).toEqual(0)
    })
  })
  describe('computeScaleIndex', () => {
    it('returns neutral color index when there is 0% difference', () => {
      expect(computeScaleIndex(0, 0, tempColorScale)).toEqual(neutralIndex)
    })
    it('returns coolest color index when there is largest negative % difference', () => {
      expect(computeScaleIndex(-100, 3, tempColorScale)).toEqual(0)
    })
    it('returns warmest color index when there is largest positive % difference', () => {
      expect(computeScaleIndex(100, 3, tempColorScale)).toEqual(tempColorScale.length - 1)
    })
  })
})
