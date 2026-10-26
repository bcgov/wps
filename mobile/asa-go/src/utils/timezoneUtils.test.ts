import { DateTime } from 'luxon'
import { formatDatetimeInBCTime, getBCTimezoneLabel } from '@/utils/timezoneUtils'

describe('getBCTimezoneLabel', () => {
  it('should be PDT before BC moved to permanent Pacific Time', () => {
    expect(getBCTimezoneLabel('2026-10-31')).toEqual('PDT')
    expect(getBCTimezoneLabel('2026-01-15')).toEqual('PDT')
  })
  it('should be PCT once BC moved to permanent Pacific Time', () => {
    expect(getBCTimezoneLabel('2026-11-01')).toEqual('PCT')
    expect(getBCTimezoneLabel('2027-07-01')).toEqual('PCT')
  })
})

describe('formatDatetimeInBCTime', () => {
  it('should format in UTC-7 with a BC timezone label regardless of the input zone', () => {
    const pdt = DateTime.fromISO('2026-07-15T21:30:00Z', { zone: 'America/Edmonton' })
    expect(formatDatetimeInBCTime(pdt)).toMatch(/July 15, 2026.*2:30.*PDT$/)
    const pct = DateTime.fromISO('2026-11-02T21:30:00Z', { zone: 'America/Toronto' })
    expect(formatDatetimeInBCTime(pct)).toMatch(/November 2, 2026.*2:30.*PCT$/)
  })
  it('should use the UTC-7 date for the label', () => {
    // Oct 31 at 23:30 in UTC-8 is Nov 1 in UTC-7
    expect(formatDatetimeInBCTime(DateTime.fromISO('2026-11-01T07:30:00Z'))).toMatch(/PCT$/)
  })
})
