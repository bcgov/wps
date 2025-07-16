import { FireZoneHFIStats } from "@/api/fbaAPI"
import { getTopFuelsByArea, getTopFuelsByProportion, getZoneMinWindStatsText } from "@/utils/advisoryTextUtils"
import { DateTime } from "luxon"

const createDateTime = (year: number, month: number, day: number) => {
  return DateTime.fromObject({ year, month, day })
}

const preCoreSeasonForDate = createDateTime(2025, 5, 31)
const firstCoreSeasonDate = createDateTime(2025, 6, 1)
const lastCoreSeasonDate = createDateTime(2025, 9, 30)
const postCoreSeasonDate = createDateTime(2025, 10, 1)

const fireZoneFuelStats: FireZoneHFIStats = {
  fuel_area_stats: [
    {
      fuel_type: {
        fuel_type_id: 2,
        fuel_type_code: 'C-2',
        description: 'Boreal Spruce'
      },
      threshold: {
        id: 1,
        name: 'advisory',
        description: '4000 < hfi < 10000'
      },
      critical_hours: {
        start_time: 10.0,
        end_time: 21.0
      },
      area: 500,
      fuel_area: 1000
    },
    {
      fuel_type: {
        fuel_type_id: 2,
        fuel_type_code: 'C-2',
        description: 'Boreal Spruce'
      },
      threshold: {
        id: 2,
        name: 'warning',
        description: '4000 < hfi < 10000'
      },
      critical_hours: {
        start_time: 10.0,
        end_time: 21.0
      },
      area: 400,
      fuel_area: 1000
    },
    {
      fuel_type: {
        fuel_type_id: 9,
        fuel_type_code: 'S-1',
        description: 'Slash'
      },
      threshold: {
        id: 1,
        name: 'advisory',
        description: '4000 < hfi < 10000'
      },
      critical_hours: {
        start_time: 10.0,
        end_time: 21.0
      },
      area: 300,
      fuel_area: 1000
    },
    {
      fuel_type: {
        fuel_type_id: 4,
        fuel_type_code: 'M-1/M-2',
        description: 'mixed'
      },
      threshold: {
        id: 1,
        name: 'advisory',
        description: '4000 < hfi < 10000'
      },
      critical_hours: {
        start_time: 10.0,
        end_time: 21.0
      },
      area: 50,
      fuel_area: 100
    }
  ],
  min_wind_stats: []
}

describe('getTopFuelsByArea', () => {
  it('should return the top fuels by area before start of core season, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats, preCoreSeasonForDate)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 3))
  })
  it('should return the top fuels by area from start of core season, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats, firstCoreSeasonDate)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual([...fireZoneFuelStats.fuel_area_stats.slice(0, 2)])
  })
  it('should return the top fuels by area until end of core season, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats, lastCoreSeasonDate)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 2))
  })
  it('should return the top fuels by area after end of core season, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats, postCoreSeasonDate)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 3))
  })
})

describe('getTopFuelsByProportion', () => {
  it('should return the top fuels by proportion of their fuel area', () => {
    const result = getTopFuelsByProportion(fireZoneFuelStats.fuel_area_stats)
    // should return the fuel records that cumulatively sum to > 90% of their own fuel area
    console.log(result)
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 2))
  })
})

describe('getZoneMinWindStats', () => {
  it('should return the minimum wind speed', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 1
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 2
      }
    ])
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })
  it('should return the minimum wind speed when they are the same', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 1
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 1
      }
    ])
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })
  it('should return just advisory min wind speed', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 1
      }
    ])
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })

  it('should return just warning min wind speed', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 1
      }
    ])
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })

  it('should return specific text when both min wind speeds are 0 or round to 0', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 0.1
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 0
      }
    ])
    expect(result).toEqual('if winds exceed 0 km/h')
  })
  it('should return specific text when only advisory min wind speed is 0', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 0
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 1
      }
    ])
    expect(result).toEqual(`if winds exceed 0 km/h`)
  })
  it('should return specific text when only warning min wind speed is 0', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 1
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 0
      }
    ])
    expect(result).toEqual(`if winds exceed 0 km/h`)
  })
})