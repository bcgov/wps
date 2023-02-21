import React from 'react'
import { render, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ModelChoice, ModelChoices } from 'api/nextCastAPI'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'

describe('WeatherModelDropdown', () => {
  it('should call selected model handler when new model selected', async () => {
    const handleSelectedModelTypeMock = jest.fn()

    const { getByTestId } = render(
      <WeatherModelDropdown
        selectedModelType={ModelChoice.HRDPS}
        weatherModelOptions={ModelChoices}
        setSelectedModelType={handleSelectedModelTypeMock}
      />
    )

    const autocomplete = getByTestId('weather-model-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    autocomplete.focus()
    userEvent.type(autocomplete, ModelChoice.RDPS)
    userEvent.type(autocomplete, '{arrowdown}')
    userEvent.type(autocomplete, '{enter}')

    await waitFor(() => expect(input.value).toBe(ModelChoice.RDPS))
    await waitFor(() => expect(handleSelectedModelTypeMock).toBeCalledTimes(1))

    await waitFor(() => expect(handleSelectedModelTypeMock).toBeCalledWith(ModelChoice.RDPS))
  })
})
