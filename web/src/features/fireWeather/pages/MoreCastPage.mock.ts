import { ModelsResponse, ModelSummariesResponse } from 'api/modelAPI'
import { ObservationsResponse } from 'api/observationAPI'
import { ForecastResponse, ForecastSummariesResponse } from 'api/forecastAPI'
import moment from 'moment'

const mockNow = moment()
  .utc()
  .set({ hour: 0, minute: 0, second: 0 })

const mockPast = mockNow.subtract(2, 'days')

export const mockStations = [
  { code: 1, name: 'Station 1', lat: 1, long: 1 },
  { code: 2, name: 'Station 2', lat: 2, long: 2 }
]

export const emptyModelsResponse = {
  predictions: []
}

export const mockModelsResponse: RecursivePartial<ModelsResponse> = {
  predictions: [
    {
      station: mockStations[0],
      values: [
        {
          datetime: mockNow.format(),
          temperature: 7.4,
          relative_humidity: 69,
          wind_direction: 230,
          wind_speed: 5,
          total_precipitation: 0
        },
        {
          datetime: mockNow.add(3, 'hours').format(),
          temperature: 17.4,
          relative_humidity: 80,
          wind_direction: 234,
          wind_speed: 8,
          total_precipitation: 0
        }
      ]
    }
  ]
}

export const emptyObservationsResponse = {
  hourlies: []
}

export const mockObservationsResponse: RecursivePartial<ObservationsResponse> = {
  hourlies: [
    {
      station: mockStations[0],
      values: [
        {
          datetime: mockPast.format(),
          temperature: 16.9,
          relative_humidity: 37.0,
          wind_speed: 9.0,
          wind_direction: 45.0,
          barometric_pressure: 0.0,
          precipitation: 0.0,
          ffmc: undefined,
          isi: undefined,
          fwi: undefined
        },
        {
          datetime: mockPast.add(1, 'hours').format(),
          temperature: 19.9,
          relative_humidity: 45.0,
          wind_speed: 9.0,
          wind_direction: 45.0,
          barometric_pressure: 0.0,
          precipitation: 0.0,
          ffmc: undefined,
          isi: undefined,
          fwi: undefined
        }
      ]
    }
  ]
}

export const emptyModelSummariesResponse = {
  summaries: []
}

export const mockModelSummariesResponse: RecursivePartial<ModelSummariesResponse> = {
  summaries: [
    {
      station: mockStations[0],
      model: { name: 'Global Deterministic Prediction System', abbrev: 'GDPS' },
      values: [
        {
          datetime: mockPast.format(),
          tmp_tgl_2_5th: 20.0,
          tmp_tgl_2_90th: 24.0,
          tmp_tgl_2_median: 23.0,
          rh_tgl_2_5th: 52.0,
          rh_tgl_2_90th: 73.0,
          rh_tgl_2_median: 61.0
        },
        {
          datetime: mockPast.add(1, 'hours').format(),
          tmp_tgl_2_5th: 20.3,
          tmp_tgl_2_90th: 23.3,
          tmp_tgl_2_median: 22.3,
          rh_tgl_2_5th: 64.3,
          rh_tgl_2_90th: 81.3,
          rh_tgl_2_median: 72.4
        }
      ]
    }
  ]
}

export const emptyForecastsResponse = {
  noon_forecasts: []
}

export const mockForecastsResponse: RecursivePartial<ForecastResponse> = {
  noon_forecasts: [
    {
      station_code: mockStations[0]['code'],
      values: [
        {
          datetime: mockNow.format(),
          temperature: 21,
          relative_humidity: 38,
          wind_direction: 290,
          wind_speed: 5.5,
          total_precipitation: 0.0,
          gc: undefined,
          ffmc: 87.398,
          dmc: 50.918,
          dc: 550.5439,
          isi: 5.97819,
          bui: 82.7119,
          fwi: 19.99413,
          danger_rating: 2,
          created_at: mockNow.format()
        },
        {
          datetime: mockNow.add(1, 'days').format(),
          temperature: 24,
          relative_humidity: 38,
          wind_direction: 290,
          wind_speed: 5.5,
          total_precipitation: 0.0,
          gc: undefined,
          ffmc: 87.398,
          dmc: 50.918,
          dc: 550.5439,
          isi: 5.97819,
          bui: 82.7119,
          fwi: 19.99413,
          danger_rating: 2,
          created_at: '2020-07-21T15:30:00'
        }
      ]
    }
  ]
}

export const mockForecastSummariesResponse: RecursivePartial<ForecastSummariesResponse> = {
  summaries: [
    {
      station: mockStations[0],
      values: [
        {
          datetime: mockPast.format(),
          tmp_max: 24,
          tmp_min: 21,
          rh_max: 44,
          rh_min: 43
        }
      ]
    }
  ]
}

export const emptyForecastSummariesResponse = {
  summaries: []
}

const modelRun = {
  datetime: mockPast.format(),
  name: 'Global Deterministic Prediction System',
  abbreviation: 'GDPS',
  projection: 'latlon.15x.15'
}
export const mockRecentHistoricModelsResponse = {
  predictions: [
    {
      station: mockStations[0],
      model_run: modelRun,
      values: [
        {
          datetime: mockPast.format(),
          temperature: 20,
          relative_humidity: 45
        }
      ]
    },
    {
      station: mockStations[0],
      model_run: modelRun,
      values: [
        {
          datetime: mockPast.add(3, 'hours').format(),
          temperature: 17,
          relative_humidity: 60
        }
      ]
    }
  ]
}

export const mockRecentModelsResponse = {
  stations: [
    {
      station: mockStations[0],
      model_runs: [
        {
          model_run: modelRun,
          values: [
            {
              datetime: mockPast.format(),
              bias_adjusted_temperature: 30,
              bias_adjusted_relative_humidity: 55
            },
            {
              datetime: mockPast.add(3, 'hours').format(),
              bias_adjusted_temperature: 28,
              bias_adjusted_relative_humidity: 80
            }
          ]
        }
      ]
    }
  ]
}

export const emptyRecentHistoricModelsResponse = {
  predictions: []
}

export const emptyRecentModelsResponse = {
  stations: []
}
