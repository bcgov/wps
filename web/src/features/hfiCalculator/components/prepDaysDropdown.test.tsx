import { render, fireEvent, within, waitFor } from '@testing-library/react'
import PrepDaysDropdown from 'features/hfiCalculator/components/PrepDaysDropdown'
import React from 'react'
describe('PrepDayDropdown', () => {
  it('should render with the default value', async () => {
    const setNumDaysMock = jest.fn()
    const { getByTestId } = render(
      <PrepDaysDropdown days={5} setNumPrepDays={setNumDaysMock} />
    )
    const autocomplete = getByTestId('prep-days-dropdown')
    const input = within(autocomplete).getByRole('textbox') as HTMLInputElement

    await waitFor(() => expect(input.value).toBe('5'))
    await waitFor(() => expect(setNumDaysMock).toBeCalledTimes(0))
  })
  it('should change when input is changed', async () => {
    const setNumDaysMock = jest.fn()
    const { getByTestId } = render(
      <PrepDaysDropdown days={5} setNumPrepDays={setNumDaysMock} />
    )
    const autocomplete = getByTestId('prep-days-dropdown')
    const input = within(autocomplete).getByRole('textbox') as HTMLInputElement

    autocomplete.focus()
    // assign value to input field
    fireEvent.change(input, { target: { value: '3' } })
    fireEvent.keyDown(autocomplete, { key: 'ArrowDown' })
    fireEvent.keyDown(autocomplete, { key: 'Enter' })

    await waitFor(() => expect(input.value).toBe('3'))
    await waitFor(() => expect(setNumDaysMock).toBeCalledTimes(1))
  })
})
