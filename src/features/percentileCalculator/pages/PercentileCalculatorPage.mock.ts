import { PercentilesResponse } from 'api/percentileAPI'

export const mockStations = [
  { code: 1, name: 'Station 1' },
  { code: 2, name: 'Station 2' }
]

export const mockPercentilesResponse: PercentilesResponse = {
  stations: {
    [mockStations[0].code]: {
      ffmc: 94.95859222412109,
      isi: 15.589389991760253,
      bui: 157.5261016845703,
      season: { start_month: 5, start_day: 1, end_month: 8, end_day: 31 },
      years: [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019],
      station: { name: mockStations[0].name, code: mockStations[0].code }
    },
    [mockStations[1].code]: {
      ffmc: 90.95859222412109,
      isi: 10.589389991760253,
      bui: 159.5261016845703,
      season: { start_month: 5, start_day: 1, end_month: 8, end_day: 31 },
      years: [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019],
      station: { name: mockStations[1].name, code: mockStations[1].code }
    }
  },
  mean_values: {
    ffmc: 93.95859222412109,
    isi: 12.589389991760253,
    bui: 158.5261016845703
  },
  year_range: { start: 2010, end: 2019 },
  percentile: 90
}
