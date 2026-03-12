import {
  combineCSSClassNames,
  isEndOfRange,
  isRangeSameDay,
  isSameRange,
  isStartOfRange,
  parseOptionalDate
} from 'components/dateRangePicker/utils'
import { addYears } from 'date-fns'
describe('DateRangePicker - utils', () => {
  describe('isRangeSameDay', () => {
    it('should return true for same day', () => {
      const sameDate = '2021/11/29'
      const startDate = new Date(sameDate)
      const endDate = new Date(sameDate)

      const result = isRangeSameDay({ startDate, endDate })
      expect(result).toBe(true)
    })
    it('should return false for different days', () => {
      const startDate = new Date('2021/11/29')
      const endDate = new Date('2021/11/30')

      const result = isRangeSameDay({ startDate, endDate })
      expect(result).toBe(false)
    })
    it('should return false if start is undefined', () => {
      const endDate = new Date('2021/11/30')

      const result = isRangeSameDay({ startDate: undefined, endDate })
      expect(result).toBe(false)
    })
    it('should return false if start and end are undefined', () => {
      const result = isRangeSameDay({ startDate: undefined, endDate: undefined })
      expect(result).toBe(false)
    })
  })
  describe('parseOptionalDate', () => {
    const dateString = '2021/11/29'
    const startDate = new Date(dateString)
    const defaultDate = addYears(startDate, 10)
    it('should return the date if valid', () => {
      const result = parseOptionalDate(startDate, defaultDate)
      expect(result).toEqual(startDate)
    })
    it('should return the default date if invalid', () => {
      const invalidDate = new Date('2021/11/229')
      const result = parseOptionalDate(invalidDate, defaultDate)
      expect(result).toEqual(defaultDate)
    })
  })

  describe('isStartOfRange', () => {
    it('should return true if day is the first day in the range', () => {
      const startDate = new Date('2021/11/29')
      const result = isStartOfRange({ startDate }, startDate)
      expect(result).toEqual(true)
    })
    it('should return false if day is not the first day in the range', () => {
      const startDate = new Date('2021/11/29')
      const endDate = new Date('2021/11/30')
      const result = isStartOfRange({ startDate, endDate }, endDate)
      expect(result).toEqual(false)
    })
    it('should return false if date range is undefined', () => {
      const startDate = new Date('2021/11/29')
      const result = isStartOfRange({}, startDate)
      expect(result).toEqual(false)
    })
  })

  describe('isEndOfRange', () => {
    it('should return true if day is the last day in the range', () => {
      const startDate = new Date('2021/11/28')
      const endDate = new Date('2021/11/29')
      const result = isEndOfRange({ startDate, endDate }, endDate)
      expect(result).toEqual(true)
    })
    it('should return false if day is not the last day in the range', () => {
      const startDate = new Date('2021/11/29')
      const endDate = new Date('2021/11/30')
      const result = isEndOfRange({ startDate, endDate }, startDate)
      expect(result).toEqual(false)
    })
    it('should return false if date range is undefined', () => {
      const endDate = new Date('2021/11/30')
      const result = isEndOfRange({}, endDate)
      expect(result).toEqual(false)
    })
  })
  describe('combineCSSClassNames', () => {
    it('should join css class names', () => {
      const class1 = 'class1'
      const class2 = 'class2'
      const result = combineCSSClassNames(class1, class2)
      expect(result).toEqual('class1 class2')
    })
    it('should return empty string if no class names', () => {
      const result = combineCSSClassNames()
      expect(result).toEqual('')
    })
    it('should return single class name if only one class', () => {
      const class1 = 'class1'
      const result = combineCSSClassNames(class1)
      expect(result).toEqual(class1)
    })
  })
  describe('isSameRange', () => {
    it('should return true for a same range', () => {
      const startDate = new Date('2021/11/28')
      const endDate = new Date('2021/11/29')
      const result = isSameRange({ startDate, endDate }, { startDate, endDate })
      expect(result).toEqual(true)
    })
    it('should return false for different ranges', () => {
      const startDate = new Date('2021/11/28')
      const endDate = new Date('2021/11/29')
      const differentEndDate = new Date('2021/11/30')
      const result = isSameRange({ startDate, endDate }, { startDate, endDate: differentEndDate })
      expect(result).toEqual(false)
    })
    it('should return false for empty ranges', () => {
      const result = isSameRange({}, {})
      expect(result).toEqual(false)
    })
  })
})
