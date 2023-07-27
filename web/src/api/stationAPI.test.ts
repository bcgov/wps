import { StationGroupMember, getStationGroupsMembers } from 'api/stationAPI'
import axios from 'api/axios'

describe('stationAPI', () => {
  it('should return groups from group endpoint', async () => {
    const mockMemberStation: StationGroupMember = {
      id: '1',
      display_label: '',
      fire_centre: { id: '', display_label: '' },
      fire_zone: { id: '', display_label: '', fire_centre: '' },
      station_code: 0,
      station_status: 'ACTIVE'
    }
    axios.post = vi.fn().mockResolvedValue({ data: { stations: [mockMemberStation] } })
    const res = await getStationGroupsMembers(['1'])
    expect(res).toHaveLength(1)
    expect(res[0].id).toBe('1')
  })
})
