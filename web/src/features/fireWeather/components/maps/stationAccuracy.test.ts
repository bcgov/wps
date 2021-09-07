import {
  StationMetrics,
  neutralColor,
  noDataColor,
  tempColorScale,
  rhColorScale,
  neutralIndex,
  computeTempAccuracyColor,
  computeTempAccuracySize,
  computeTempScaleIndex,
  computeRHAccuracyColor,
  computeRHAccuracySize,
  computeRHScaleIndex,
  computeStroke,
  determineMarkerRadius,
  darkOrangeColor,
  darkGreenColor,
  lightGreenColor,
  middleOrangeColor,
  darkRedColor,
  darkBlueColor,
  pinkColor
} from 'features/fireWeather/components/maps/stationAccuracy'

describe('Station map color accuracy', () => {
  const nullObs: StationMetrics = {
    observations: null,
    forecasts: {
      temperature: 15,
      relative_humidity: 20
    }
  }
  const nullForecast: StationMetrics = {
    forecasts: null,
    observations: {
      temperature: 20,
      relative_humidity: 30
    }
  }
  const perfectForecast: StationMetrics = {
    observations: {
      relative_humidity: 30,
      temperature: 0
    },
    forecasts: {
      relative_humidity: 30,
      temperature: 0
    }
  }
  describe('computeRHScaleIndex', () => {
    it('should return the neutral index when observed and forecast RH are equal', () => {
      expect(computeRHScaleIndex(100, 100)).toEqual(neutralIndex)
    })

    it('should return the largest scale index when observed RH is much lower than forecasted RH', () => {
      expect(computeRHScaleIndex(100, 10)).toEqual(rhColorScale.length - 1)
    })

    it('should return a scale index of 0 when observed RH is much greater than forecasted RH', () => {
      expect(computeRHScaleIndex(10, 100)).toEqual(0)
    })

    it('should return a scale index of neutralIndex+1 when observed RH is 4 percentage points lower than forecasted RH', () => {
      expect(computeRHScaleIndex(80, 76)).toEqual(neutralIndex + 1)
    })

    it('should return a scale index of neutralIndex-2 when observed RH is 8 percentage points greater than forecasted RH', () => {
      expect(computeRHScaleIndex(50, 58)).toEqual(neutralIndex - 2)
    })
  })

  describe('computeTempScaleIndex', () => {
    it('should return neutral index when observed and forecast temp are equal', () => {
      expect(computeTempScaleIndex(20, 20)).toEqual(neutralIndex)
    })

    it('should return the largest scale index when observed temp is much lower than forecasted temp', () => {
      expect(computeTempScaleIndex(40, 0)).toEqual(tempColorScale.length - 1)
    })

    it ('should return a scale index of 0 when observed temp is much greater than forecasted temp', () => {
      expect(computeTempScaleIndex(30, 0)).toEqual(0)
    })

    it('should return a scale index of neutralIndex+1 when observed temp is 3 degrees lower than forecasted temp', () => {
      expect(computeTempScaleIndex(20, 17)).toEqual(neutralIndex+1)
    })

    it('should return a scale index of neutralIndex-2 when observed temp is 5 degrees higher than forecasted temp', () => {
      expect(computeTempScaleIndex(20, 25)).toEqual(neutralIndex - 2)
    })
  })

  describe('computeRHAccuracyColor', () => {
    it('should return the no data color code when forecasted is null', () => {
      expect(computeRHAccuracyColor(nullForecast)).toEqual(noDataColor)
    })

    it('should return the no data color code when observation is null', () => {
      expect(computeRHAccuracyColor(nullObs)).toEqual(noDataColor)
    })

    it('should return the neutral color code when forecasted and observed RH are equal', () => {
      expect(computeRHAccuracyColor(perfectForecast)).toEqual(neutralColor)
    })

    it('should return the warmest color code when observed RH is much lower than forecasted RH', () => {
      const overForecastedRH: StationMetrics = {
        observations: {
          relative_humidity: 10,
          temperature: 0
        },
        forecasts: {
          relative_humidity: 60,
          temperature: 0
        }
      }
      expect(computeRHAccuracyColor(overForecastedRH)).toEqual(darkOrangeColor)
    })

    it('should return the coldest color code when observed RH is much higher than forecasted RH', () => {
      const underForecastedRH: StationMetrics = {
        observations: {
          relative_humidity: 60,
          temperature: 0
        },
        forecasts: {
          relative_humidity: 10,
          temperature: 0
        }
      }
      expect(computeRHAccuracyColor(underForecastedRH)).toEqual(darkGreenColor)
    })

    it('should return a lightly cool color code when observed RH is 4 points higher than forecasted RH', () => {
      const slightlyUnderForecastedRH: StationMetrics = {
        observations: {
          relative_humidity: 54,
          temperature: 0
        },
        forecasts: {
          relative_humidity: 50,
          temperature: 0
        }
      }
      expect(computeRHAccuracyColor(slightlyUnderForecastedRH)).toEqual(lightGreenColor)
    })

    it('should return the medium warm color code when observed RH is 7 points lower than forecasted RH', () => {
      const overForecastedRH: StationMetrics = {
        observations: {
          relative_humidity: 30,
          temperature: 0
        },
        forecasts: {
          relative_humidity: 37,
          temperature: 0
        }
      }
      expect(computeRHAccuracyColor(overForecastedRH)).toEqual(middleOrangeColor)
    })

    it('should return the neutral color code when observed RH is within 3 points of forecasted RH', () => {
      let goodForecast: StationMetrics = {
        observations: {
          relative_humidity: 20,
          temperature: 0
        },
        forecasts: {
          relative_humidity: 23,
          temperature: 0
        }
      }
      expect(computeRHAccuracyColor(goodForecast)).toEqual(neutralColor)
      goodForecast = {
        observations: {
          relative_humidity: 20,
          temperature: 0
        },
        forecasts: {
          relative_humidity: 17,
          temperature: 0
        }
      }
      expect(computeRHAccuracyColor(goodForecast)).toEqual(neutralColor)
    })
  })

  describe('computeTempAccuracyColor', () => {
    it('should return the no data color code when forecast is null', () => {
      expect(computeTempAccuracyColor(nullForecast)).toEqual(noDataColor)
    })

    it('should return the no data color code when observation is null', () => {
      expect(computeTempAccuracyColor(nullObs)).toEqual(noDataColor)
    })

    it('should return the neutral color code when observed and forecast temp are equal', () => {
      expect(computeTempAccuracyColor(perfectForecast)).toEqual(neutralColor)
    })

    it('should return the darkest red color code when forecasted temp is much lower than observed', () => {
      const underForecastedTemp: StationMetrics = {
        forecasts: {
          temperature: 15,
          relative_humidity: 0
        },
        observations: {
          temperature: 35,
          relative_humidity: 0
        }
      }
      expect(computeTempAccuracyColor(underForecastedTemp)).toEqual(darkRedColor)
    })

    it('should return the darkest blue color code when forecasted temp is much higher than observed', () => {
      const overForecastedTemp: StationMetrics = {
        forecasts: {
          temperature: 40,
          relative_humidity: 0
        },
        observations: {
          temperature: 10,
          relative_humidity: 0
        }
      }
      expect(computeTempAccuracyColor(overForecastedTemp)).toEqual(darkBlueColor)
    })

    it('should return pale pink color code when observed temp is 3 degrees warmer than forecasted temp', () => {
      const forecastTooLow: StationMetrics = {
        forecasts: {
          temperature: 20,
          relative_humidity: 0
        },
        observations: {
          temperature: 23,
          relative_humidity: 0
        }
      }
      expect(computeTempAccuracyColor(forecastTooLow)).toEqual(pinkColor)
    })
  })





  
})
