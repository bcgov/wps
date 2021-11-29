import { render, fireEvent } from '@testing-library/react'
import DatePicker from 'components/DatePicker'
import React from 'react'

describe('DatePicker', () => {
  const defaultDate = '2021/11/29'
  const hotDayInAugust = '2021/08/04'
  const hotDayInAugustPST = '2021-08-04T00:00:00.000-08:00'

  const setup = (updateDateFn: jest.Mock<void, []>) => {
    const utils = render(<DatePicker date={defaultDate} updateDate={updateDateFn} />)
    const datePicker = utils.getByRole('textbox') as HTMLInputElement
    return datePicker
  }
  it('should set the default date in UTC-8', () => {
    const updateDateStub = jest.fn((): void => {
      /** no op */
    })
    const datePicker = setup(updateDateStub)
    expect(datePicker).toHaveValue(defaultDate)
  })
  it('should set the default date in UTC-8 when changed', () => {
    const updateDateStub = jest.fn((): void => {
      /** no op */
    })
    const datePicker = setup(updateDateStub)
    fireEvent.change(datePicker, { target: { value: hotDayInAugust } })
    expect(datePicker).toHaveValue(hotDayInAugust)
  })
  it.only('should set the default date in UTC-8 when enter pressed', () => {
    const updateDateStub = jest.fn((): void => {
      /** no op */
    })
    const datePicker = setup(updateDateStub)

    datePicker.value = hotDayInAugust
    fireEvent.keyDown(datePicker, { key: 'Enter', code: 'Enter', charCode: 13 })
    expect(datePicker).toHaveValue(hotDayInAugust)
    expect(updateDateStub).toBeCalledWith(hotDayInAugustPST)
  })
  it('should set the default date in UTC-8 when onBlur', () => {
    const updateDateStub = jest.fn((): void => {
      /** no op */
    })
    const datePicker = setup(updateDateStub)

    datePicker.value = hotDayInAugust
    fireEvent.blur(datePicker)
    expect(datePicker).toHaveValue(hotDayInAugust)
    expect(updateDateStub).toBeCalledWith(hotDayInAugustPST)
  })
})
