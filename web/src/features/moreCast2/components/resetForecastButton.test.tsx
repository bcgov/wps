import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import store from 'app/store'
import ResetForecastButton, { ResetForecastButtonProps } from 'features/moreCast2/components/ResetForecastButton'
import React from 'react'
import { Provider } from 'react-redux'

describe('SaveForecastButton', () => {
  const mockHandleResetClick = jest.fn()
  const mockHandleResetButtonConfirm = jest.fn()
  const mockSetShowResetDialog = jest.fn()

  const defaultProps: ResetForecastButtonProps = {
    enabled: true,
    label: 'Reset',
    showResetDialog: false,
    setShowResetDialog: mockSetShowResetDialog,
    handleResetButtonConfirm: mockHandleResetButtonConfirm,
    onClick: mockHandleResetClick
  }

  it('should render the button as enabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton {...defaultProps} />
      </Provider>
    )

    const resetForecastButton = getByTestId('reset-forecast-button')
    expect(resetForecastButton).toBeInTheDocument()
    expect(resetForecastButton).toBeEnabled()
  })
  it('should render the button as disabled', () => {
    const propsWithEnabledFalse = { ...defaultProps, enabled: false }
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton {...propsWithEnabledFalse} />
      </Provider>
    )

    const manageStationsButton = getByTestId('reset-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeDisabled()
  })
  it('should call the reset click handler when clicked', async () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton {...defaultProps} />
      </Provider>
    )
    const resetForecastButton = getByTestId('reset-forecast-button')
    userEvent.click(resetForecastButton)
    await waitFor(() => expect(mockHandleResetClick).toHaveBeenCalledTimes(1))
  })
  it('should call the reset button confirm handler when Confirm is clicked', async () => {
    const propsWithResetDialog = { ...defaultProps, showResetDialog: true }
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton {...propsWithResetDialog} />
      </Provider>
    )
    const resetDialog = getByTestId('reset-dialog')
    expect(resetDialog).toBeInTheDocument()
    const confirmButton = getByTestId('reset-forecast-confirm-button')
    userEvent.click(confirmButton)
    await waitFor(() => expect(mockHandleResetButtonConfirm).toHaveBeenCalledTimes(1))
  })
  it('should close the dialog when the Cancel button is clicked', async () => {
    const propsWithResetDialog = { ...defaultProps, showResetDialog: true }
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton {...propsWithResetDialog} />
      </Provider>
    )
    const cancelButton = getByTestId('reset-forecast-cancel-button')
    userEvent.click(cancelButton)
    await waitFor(() => expect(mockSetShowResetDialog).toHaveBeenCalledWith(false))
  })
})
