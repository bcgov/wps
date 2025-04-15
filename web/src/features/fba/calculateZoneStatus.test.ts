import { AdvisoryMinWindStats } from '@/api/fbaAPI'
import { getWindSpeedMinimum } from '@/features/fba/calculateZoneStatus'

describe('getWindSpeedMinimum', () => {
  const advisoryThreshold = {
    id: 1,
    name: 'Advisory',
    description: 'Advisory threshold'
  }

  const warningThreshold = {
    id: 2,
    name: 'Warning',
    description: 'Warning threshold'
  }

  it('returns the lower of two valid wind speeds', () => {
    const input: AdvisoryMinWindStats[] = [
      { threshold: advisoryThreshold, min_wind_speed: 12 },
      { threshold: warningThreshold, min_wind_speed: 8 }
    ]
    expect(getWindSpeedMinimum(input)).toBe(8)
  })

  it('returns the advisory wind speed if warning is missing', () => {
    const input: AdvisoryMinWindStats[] = [{ threshold: advisoryThreshold, min_wind_speed: 10 }]
    expect(getWindSpeedMinimum(input)).toBe(10)
  })

  it('returns the warning wind speed if advisory is missing', () => {
    const input: AdvisoryMinWindStats[] = [{ threshold: warningThreshold, min_wind_speed: 7 }]
    expect(getWindSpeedMinimum(input)).toBe(7)
  })

  it('ignores wind speeds <= 0', () => {
    const input: AdvisoryMinWindStats[] = [
      { threshold: advisoryThreshold, min_wind_speed: 0 },
      { threshold: warningThreshold, min_wind_speed: -5 }
    ]
    expect(getWindSpeedMinimum(input)).toBeUndefined()
  })

  it('returns undefined if both min_wind_speed values are missing', () => {
    const input: AdvisoryMinWindStats[] = [{ threshold: advisoryThreshold }, { threshold: warningThreshold }]
    expect(getWindSpeedMinimum(input)).toBeUndefined()
  })

  it('returns undefined if input array is empty', () => {
    expect(getWindSpeedMinimum([])).toBeUndefined()
  })
})
