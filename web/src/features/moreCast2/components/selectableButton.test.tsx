import { render, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import SelectableButton from 'features/moreCast2/components/SelectableButton'


describe('SelectableButton', () => {
  it('should render the button as selected', () => {
    const selectHandler = vi.fn()
    const { getByTestId } = render(
      <SelectableButton dataTestId="temp-tab-button" onClick={selectHandler} selected={true} weatherParam="temp">
        Temp
      </SelectableButton>
    )

    const selectableButton = getByTestId('temp-tab-button-selected')
    expect(selectableButton).toBeInTheDocument()
    expect(selectableButton).toBeEnabled()
  })
  it('should render the button as unselected', () => {
    const selectHandler = vi.fn()
    const { getByTestId } = render(
      <SelectableButton dataTestId="temp-tab-button" onClick={selectHandler} selected={false} weatherParam="temp">
        Temp
      </SelectableButton>
    )

    const selectableButton = getByTestId('temp-tab-button-unselected')
    expect(selectableButton).toBeInTheDocument()
    expect(selectableButton).toBeEnabled()
  })

  it('should call the toggle callback when clicked', async () => {
    const selectHandler = vi.fn()
    const { getByTestId } = render(
      <SelectableButton dataTestId="temp-tab-button" onClick={selectHandler} selected={false} weatherParam="temp">
        Temp
      </SelectableButton>
    )

    const selectableButton = getByTestId('temp-tab-button-unselected')
    await userEvent.click(selectableButton)
    await waitFor(() => expect(selectHandler).toHaveBeenCalledTimes(1))
  })
})
