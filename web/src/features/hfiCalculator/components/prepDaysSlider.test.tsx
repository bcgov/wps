import { render, screen, fireEvent } from '@testing-library/react'
import PrepDaysSlider from 'features/hfiCalculator/components/PrepDaysSlider'
import React from 'react'
describe('PrepDaySlider', () => {
  it('should render the status if it is defined', () => {
    const setDaysMock = jest.fn()
    const { getAllByDisplayValue } = render(
      <PrepDaysSlider days={2} setDays={setDaysMock} />
    )
    expect(getAllByDisplayValue(2)[0]).toHaveAttribute('name', 'input-prep-days-input')
    expect(setDaysMock.mock.calls.length).toBe(0)
  })
  it.only('should change when input is changed', () => {
    const setDaysMock = jest.fn()
    const { getAllByDisplayValue } = render(
      <PrepDaysSlider days={2} setDays={setDaysMock} />
    )
    const input = screen.getByTestId('prep-days-slider')
    console.log(input.nextSibling)
    const slider = getAllByDisplayValue(2)[0]
    fireEvent.change(slider, { target: { value: 5 } })

    expect(setDaysMock).toBeCalledTimes(1)
  })
})
