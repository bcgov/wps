import { FireZoneFuelStats } from '@/api/fbaAPI'
import { getMinStartAndMaxEndTime } from '@/features/fba/criticalHoursStartEndTime'

const sameDayC2: FireZoneFuelStats = {
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
}

const fullDayC2: FireZoneFuelStats = {
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
    start_time: 7.0,
    end_time: 7.0
  },
  area: 400,
  fuel_area: 1000
}

const nextDayS1: FireZoneFuelStats = {
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
    start_time: 12.0,
    end_time: 4.0
  },
  area: 90,
  fuel_area: 100
}

const nextDayM1M2: FireZoneFuelStats = {
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
    start_time: 11.0,
    end_time: 6.0
  },
  area: 50,
  fuel_area: 100
}

const noHoursM1M2: FireZoneFuelStats = {
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
    start_time: undefined,
    end_time: undefined
  },
  area: 50,
  fuel_area: 100
}

describe('getMinStartAndMaxEndTime', () => {
  it('handles normal same-day critical hours', () => {
    const result = getMinStartAndMaxEndTime([sameDayC2])
    expect(result).toEqual({ minStartTime: 10, maxEndTime: 21 })
  })
  it('handles full day/time critical hours', () => {
    const result = getMinStartAndMaxEndTime([fullDayC2])
    expect(result).toEqual({ minStartTime: 7, maxEndTime: 7 })
  })
  it('handles stats containing both same day and next day critical hours', () => {
    const result = getMinStartAndMaxEndTime([sameDayC2, fullDayC2])
    expect(result).toEqual({ minStartTime: 7, maxEndTime: 7 })
  })
  it('handles stats containing both same day and next day critical hours, as well as no critical hours', () => {
    const result = getMinStartAndMaxEndTime([sameDayC2, nextDayM1M2, nextDayS1, noHoursM1M2])
    expect(result).toEqual({ minStartTime: 10, maxEndTime: 6 })
  })
})
