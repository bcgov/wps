import selectedStationGroupsMembersSlice, {
  initialState,
  getStationGroupsMembersStart,
  getStationGroupsMembersSuccess,
  getStationGroupsMembersFailed
} from 'commonSlices/selectedStationGroupMembers'
import { StationGroupMember } from 'api/stationAPI'

describe('selectedStationGroupMembers', () => {
  it('should set loading = true when getWeatherIndeterminatesStart is called', () => {
    expect(selectedStationGroupsMembersSlice(initialState, getStationGroupsMembersStart())).toEqual({
      ...initialState,
      loading: true
    })
  })
  it('should set loading = false when getWeatherIndeterminatesSuccess is called', () => {
    expect(selectedStationGroupsMembersSlice(initialState, getStationGroupsMembersSuccess([]))).toEqual({
      ...initialState,
      loading: false
    })
  })
  it('should set the station group members when getWeatherIndeterminatesSuccess is called', () => {
    const stationGroupMember: StationGroupMember = {
      id: '1',
      display_label: 'one',
      fire_centre: { id: '1', display_label: 'fc1' },
      fire_zone: {
        id: '1',
        display_label: 'fz1',
        fire_centre: 'fc1'
      },
      station_code: 1,
      station_status: 'active'
    }
    expect(
      selectedStationGroupsMembersSlice(initialState, getStationGroupsMembersSuccess([stationGroupMember]))
    ).toEqual({
      ...initialState,
      members: [stationGroupMember],
      loading: false
    })
  })
  it('should set a value for error state when getWeatherIndeterminatesFailed is called', () => {
    expect(selectedStationGroupsMembersSlice(initialState, getStationGroupsMembersFailed('error')).error).not.toBeNull()
  })
})
