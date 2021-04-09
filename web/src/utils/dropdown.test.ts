import { GeoJsonStation } from 'api/stationAPI'
import { getSelectedStationOptions } from 'utils/dropdown'

describe('Dropdown utils', () => {
  const testStationCode = 1
  const testStationName = 'test'
  const testStation: GeoJsonStation = {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [0, 0]
    },
    properties: {
      code: testStationCode,
      name: testStationName,
      ecodivision_name: 'test',
      core_season: { start_month: 1, start_day: 1, end_month: 1, end_day: 1 }
    }
  }
  it('should return the unknown value when there is no station in the map', () => {
    expect(getSelectedStationOptions([0], { 1: testStation })).toEqual({
      selectedStationOptions: [{ code: 0, name: 'Unknown' }],
      isThereUnknownCode: true
    })
  })
  it('should return the unknown value when there is no station in the map', () => {
    expect(getSelectedStationOptions([1], { 1: testStation })).toEqual({
      selectedStationOptions: [{ code: 1, name: testStationName }],
      isThereUnknownCode: false
    })
  })
})
