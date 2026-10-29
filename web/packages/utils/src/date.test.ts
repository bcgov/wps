import { DateTime } from 'luxon'
import {
  formatDatetimeWithTimezone,
  formatInBCPacificTime,
  formatISODateInPST,
  formatMonthAndDay,
  getBCTimezoneLabel,
  isBeforeNoonForecast,
  toBCPacificTime
} from './date'

describe('Date util functions', () => {
  describe('toBCPacificTime', () => {
    it.each([
      ['2024-01-15T07:30:00Z', '2024-01-14T23:30:00-08:00'],
      ['2024-07-15T07:30:00Z', '2024-07-15T00:30:00-07:00'],
      ['2026-11-01T09:30:00Z', '2026-11-01T02:30:00-07:00'],
      ['2027-01-15T07:30:00Z', '2027-01-15T00:30:00-07:00']
    ])('converts %s to Pacific time without changing the instant', (instant, expected) => {
      const original = DateTime.fromISO(instant, { zone: 'utc' })

      const result = toBCPacificTime(original)

      expect(result.toISO({ suppressMilliseconds: true })).toBe(expected)
      expect(result.toMillis()).toBe(original.toMillis())
    })
  })

  describe('formatDateInPST', () => {
    it('should format the date with PST timezone', () => {
      const datetime = formatISODateInPST('2021-08-02T00:00-08:00')
      expect(datetime.year).toBe(2021)
      expect(datetime.month).toBe(8)
      expect(datetime.day).toBe(2)
      expect(datetime.toFormat('yyyy-MM-dd')).toBe('2021-08-02')
    })
  })

  describe('formatMonthAndDay', () => {
    it("should format the given month and date in 'D MMMM'", () => {
      expect(formatMonthAndDay(1, 1)).toEqual('1 January')
      expect(formatMonthAndDay(1, 10)).toEqual('10 January')
      expect(formatMonthAndDay(4, 15)).toEqual('15 April')
      expect(formatMonthAndDay(9, 30)).toEqual('30 September')
    })
  })

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
  describe('isBeforeNoonForecast', () => {
    it.each([
      ['2026-07-15T19:59:00Z', true],
      ['2026-07-15T20:00:00Z', false],
      ['2026-11-15T19:59:00Z', true],
      ['2026-11-15T20:00:00Z', false]
    ])('at %s should be %s regardless of the source timezone', (instant, expected) => {
      expect(isBeforeNoonForecast(DateTime.fromISO(instant, { zone: 'America/Toronto' }))).toBe(expected)
    })
  })
  describe('formatInBCPacificTime', () => {
    it.each([
      ['2026-01-15T20:00:00Z', 'January 15, 12:00 PST'],
      ['2026-07-15T20:00:00Z', 'July 15, 13:00 PDT'],
      ['2026-11-02T20:00:00Z', 'November 2, 13:00 PCT']
    ])('formats %s in BC Pacific time regardless of the source timezone', (instant, expected) => {
      const dt = DateTime.fromISO(instant, { zone: 'Asia/Tokyo' })
      expect(formatInBCPacificTime(dt, 'MMMM d, HH:mm')).toEqual(expected)
    })
    it('should not localize the timezone label', () => {
      const dt = DateTime.fromISO('2026-07-15T20:00:00Z', { locale: 'en-GB' })
      expect(formatInBCPacificTime(dt, 'HH:mm')).toEqual('13:00 PDT')
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
})
