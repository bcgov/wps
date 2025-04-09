import { render } from '@testing-library/react'
import ResetDialog from '@/components/ResetDialog'
import { vi } from 'vitest'

const MESSAGE = "Test"

describe('ResetDialog', () => {
  it('should not render when showResetDialog is false', () => {
    const { queryByTestId } = render(
      <>
        <ResetDialog
          showResetDialog={false}
          setShowResetDialog={() => undefined}
          handleResetButtonConfirm={() => undefined}
          message={MESSAGE}
        />
      </>
    )
    const resetDialog = queryByTestId('reset-dialog')
    expect(resetDialog).not.toBeInTheDocument()
  })
  it('should render when showResetDialog is true', () => {
    const { getByTestId } = render(
      <>
        <ResetDialog
          showResetDialog={true}
          setShowResetDialog={() => undefined}
          handleResetButtonConfirm={() => undefined}
          message={MESSAGE}
        />
      </>
    )
    const resetDialog = getByTestId('reset-dialog')
    expect(resetDialog).toBeInTheDocument()
  })
  it('should display provided message', () => {
    const { getByText } = render(
      <>
        <ResetDialog
          showResetDialog={true}
          setShowResetDialog={() => undefined}
          handleResetButtonConfirm={() => undefined}
          message={MESSAGE}
        />
      </>
    )
    const message = getByText(MESSAGE)
    expect(message).toBeInTheDocument()
  })
  it('should call setShowResetDialog function when Cancel button is clicked', () => {
    const setShowResetDialogMock = vi.fn()
    const { getByTestId } = render(
      <>
        <ResetDialog
          showResetDialog={true}
          setShowResetDialog={setShowResetDialogMock}
          handleResetButtonConfirm={() => undefined}
          message={MESSAGE}
        />
      </>
    )
    const cancelButton = getByTestId('reset-dialog-cancel-button')
    cancelButton.click()
    expect(setShowResetDialogMock).toHaveBeenCalled()
  })
  it('should call handleResetButtonConfirm function when Reset button is clicked', () => {
    const handleResetButtonConfirmMock = vi.fn()
    const { getByTestId } = render(
      <>
        <ResetDialog
          showResetDialog={true}
          setShowResetDialog={() => undefined}
          handleResetButtonConfirm={handleResetButtonConfirmMock}
          message={MESSAGE}
        />
      </>
    )
    const cancelButton = getByTestId('reset-dialog-confirm-button')
    cancelButton.click()
    expect(handleResetButtonConfirmMock).toHaveBeenCalled()
  })
})