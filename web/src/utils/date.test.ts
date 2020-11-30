import { isNoonInPST, formatDateInPDT, formatMonthAndDay } from 'utils/date'

describe('Date util functions', () => {
  describe('isNoonInPST', () => {
    it('should check if the give datetime is PST noon', () => {
      expect(isNoonInPST('2020-11-25T19:00:00+00:00')).toEqual(false)
      expect(isNoonInPST('2020-11-25T20:00:00+00:00')).toEqual(true)
      expect(isNoonInPST('2020-11-25T21:00:00+00:00')).toEqual(false)
      expect(isNoonInPST('2020-11-26T20:00:00+00:00')).toEqual(true)
    })
  })

  describe('formatDateInPDT', () => {
    it("should format the given date in 'YYYY-MM-DD HH:mm'", () => {
      expect(formatDateInPDT('2020-11-24T20:00:00+00:00')).toEqual('2020-11-24 13:00')
      expect(formatDateInPDT('2020-11-25T20:00:00+00:00')).toEqual('2020-11-25 13:00')
      const d = new Date('2020-11-25T20:00:00+00:00')
      expect(formatDateInPDT(d)).toEqual('2020-11-25 13:00')
    })

    it('should format the given date based on the given format', () => {
      expect(formatDateInPDT('2020-11-25T20:00:00+00:00', 'YYYY-MM-DD')).toEqual(
        '2020-11-25'
      )
      expect(formatDateInPDT('2020-11-25T20:00:00+00:00', 'YYYY-MM-DD HH')).toEqual(
        '2020-11-25 13'
      )
      const d = new Date('2020-11-25T20:00:00+00:00')
      expect(formatDateInPDT(d, 'YYYY-MM-DD')).toEqual('2020-11-25')
    })
  })

  describe('formatMonthAndDay', () => {
    it("should format the given month and date in 'D MMMM'", () => {
      expect(formatMonthAndDay(1, 10)).toEqual('10 January')
      expect(formatMonthAndDay(4, 15)).toEqual('15 April')
      expect(formatMonthAndDay(9, 31)).toEqual('1 October')
    })
  })
})
