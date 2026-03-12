import { vi } from 'vitest'
import { render, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ModelChoice, ModelChoices } from 'api/moreCast2API'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'

describe('WeatherModelDropdown', () => {
  it('should call selected model handler when new model selected', async () => {
    const handleSelectedModelTypeMock = vi.fn()

    const { getByTestId } = render(
      <WeatherModelDropdown
        selectedModelType={ModelChoice.HRDPS_BIAS}
        weatherModelOptions={ModelChoices}
        setSelectedModelType={handleSelectedModelTypeMock}
      />
    )

    const autocomplete = getByTestId('weather-model-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement
    autocomplete.focus()
    await userEvent.type(autocomplete, ModelChoice.PERSISTENCE)
    await userEvent.type(autocomplete, '{arrowdown}')
    await userEvent.type(autocomplete, '{enter}')

    await waitFor(() => expect(input.value).toBe(ModelChoice.PERSISTENCE))
    await waitFor(() => expect(handleSelectedModelTypeMock).toHaveBeenCalledTimes(1))

    await waitFor(() => expect(handleSelectedModelTypeMock).toHaveBeenCalledWith(ModelChoice.PERSISTENCE))
  })
})
