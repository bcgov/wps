import { render } from '@testing-library/react'
import { MARKERS } from 'components/dateRangePicker/DateRangePicker'
import Month from 'components/dateRangePicker/Month'
import { DateRange, NavigationAction } from 'components/dateRangePicker/types'
import React from 'react'

describe('Month', () => {
  const startDate = new Date('2021/11/21')
  const endDate = new Date('2021/11/29')
  const setValueStub = jest.fn((date: Date): void => {
    /** no op */
  })
  const inHoverRangeStub = jest.fn((date: Date): boolean => {
    return false
  })
  const onDayClickStub = jest.fn((date: Date): void => {
    /** no op */
  })
  const onDayHover = jest.fn((date: Date): void => {
    /** no op */
  })
  const onMonthNavigate = jest.fn((marker: symbol, action: NavigationAction): void => {
    /** no op */
  })

  const setup = (
    value: Date,
    setValueStub: (date: Date) => void,
    dateRange: DateRange,
    minDate: Date,
    maxDate: Date,
    inHoverRangeStub: (date: Date) => boolean,
    onDayClickStub: (date: Date) => void,
    onDayHoverStub: (date: Date) => void,
    onMonthNavigateStub: (marker: symbol, action: NavigationAction) => void
  ) => {
    const { getByTestId } = render(
      <Month
        testId="testMonth"
        value={value}
        marker={MARKERS.FIRST_MONTH}
        dateRange={dateRange}
        minDate={minDate}
        maxDate={maxDate}
        navState={[true, true]}
        setValue={setValueStub}
        helpers={{
          inHoverRange: inHoverRangeStub
        }}
        handlers={{
          onDayClick: onDayClickStub,
          onDayHover: onDayHoverStub,
          onMonthNavigate: onMonthNavigateStub
        }}
      />
    )
    return getByTestId('testMonth')
  }
  it('should render the month', () => {
    const dateRange = { startDate, endDate }
    const month = setup(
      startDate,
      setValueStub,
      dateRange,
      startDate,
      endDate,
      inHoverRangeStub,
      onDayClickStub,
      onDayHover,
      onMonthNavigate
    )
    expect(month).toBeDefined()
    expect(setValueStub).toBeCalledTimes(0)
    expect(onDayClickStub).toBeCalledTimes(0)
    expect(onDayHover).toBeCalledTimes(0)
    expect(onMonthNavigate).toBeCalledTimes(0)
  })
})
