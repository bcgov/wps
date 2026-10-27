import { DateTime } from 'luxon'
import { formatDatetimeWithTimezone, getBCTimezoneLabel } from '@/utils/timezoneUtils'

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

describe('formatDatetimeWithTimezone', () => {
  it('should keep the datetime in its own timezone with the device timezone label', () => {
    const pdt = DateTime.fromISO('2026-07-15T20:00:00Z', { zone: 'America/Vancouver' })
    expect(formatDatetimeWithTimezone(pdt)).toMatch(/July 15, 2026.*1:00.*PDT$/)
    const mst = DateTime.fromISO('2026-11-02T20:00:00Z', { zone: 'America/Dawson_Creek' })
    expect(formatDatetimeWithTimezone(mst)).toMatch(/November 2, 2026.*1:00.*MST$/)
  })
  it('should label Pacific time as PCT from Nov 1, 2026', () => {
    const pct = DateTime.fromISO('2026-11-02T20:00:00Z', { zone: 'America/Vancouver' })
    expect(formatDatetimeWithTimezone(pct)).toMatch(/November 2, 2026.*1:00.*PCT$/)
  })
  it('should keep PST for Pacific winter times before the switch', () => {
    const pst = DateTime.fromISO('2026-01-15T20:00:00Z', { zone: 'America/Vancouver' })
    expect(formatDatetimeWithTimezone(pst)).toMatch(/January 15, 2026.*12:00.*PST$/)
  })
})
