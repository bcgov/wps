import {
  computeAccuracyColors,
  StationMetrics,
  neutralColor,
  tempColorScale,
  rhColorScale
} from './stationAccuracy'

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
describe('Station map color accuracy', () => {
  it('should return the correct color codes', () => {
    expect(computeAccuracyColors(exactForecast)).toEqual({
      temperature: neutralColor,
      relative_humidity: neutralColor
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
