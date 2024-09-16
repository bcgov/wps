import { render, waitFor } from '@testing-library/react'
import InvalidCellToolTip from '@/features/moreCast2/components/InvalidCellToolTip'
import userEvent from '@testing-library/user-event'

describe('InvalidCellToolTip', () => {
  it('should render an open tooltip only when hovered', async () => {
    const { queryByDisplayValue, findByText, getByTestId } = render(
      <InvalidCellToolTip error={'test-error'} hoverOnly={true}>
        <></>
      </InvalidCellToolTip>
    )

    const toolTip = getByTestId('validation-tooltip')

    const invisibleMessage = queryByDisplayValue('test-error')
    expect(invisibleMessage).not.toBeInTheDocument()

    userEvent.hover(toolTip)

    const visibleMessage = await findByText('test-error')

    await waitFor(() => {
      expect(visibleMessage).toBeInTheDocument()
    })
  })

  it('should render an open tooltip statically', async () => {
    const { findByText } = render(
      <InvalidCellToolTip error={'test-error'} hoverOnly={false}>
        <></>
      </InvalidCellToolTip>
    )

    const invisibleMessage = await findByText('test-error')
    expect(invisibleMessage).toBeInTheDocument()
  })
})
