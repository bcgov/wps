import { vi, describe, it, expect } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ForecastHeader from 'features/moreCast2/components/ForecastHeader'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'

describe('ForecastHeader', () => {
  const mockColumnClickHandlerProps: ColumnClickHandlerProps = {
    colDef: { field: 'testForecast', headerName: 'test' },
    contextMenu: null,
    updateColumnWithModel: vi.fn(),
    handleClose: vi.fn()
  }

  const renderForecastHeader = () => {
    return render(
      <ForecastHeader
        colDef={{ field: 'testForecast', headerName: 'test' }}
        columnClickHandlerProps={mockColumnClickHandlerProps}
      />
    )
  }

  const renderAndOpenMenu = async () => {
    const rendered = renderForecastHeader()
    const forecastButton = rendered.getByTestId('testForecast-column-header')
    await userEvent.click(forecastButton)
    await waitFor(() => expect(rendered.getByTestId('apply-to-column-menu')).toBeInTheDocument())
    return rendered
  }

  it('should render an enabled forecast button without menu enabled by default', () => {
    const { getByTestId, queryByTestId } = renderForecastHeader()

    const forecastButton = getByTestId('testForecast-column-header')
    expect(forecastButton).toBeInTheDocument()
    expect(forecastButton).toBeEnabled()
    expect(queryByTestId('apply-to-column-menu')).not.toBeInTheDocument()
  })
  it('should open apply to column menu when forecast button clicked', async () => {
    await renderAndOpenMenu()
  })
  it('should call updateColumnWithModel handler when model to apply is chosen', async () => {
    const { getByTestId } = await renderAndOpenMenu()
    const modelMenuButton = getByTestId('apply-model-to-column-button')
    expect(modelMenuButton).toBeInTheDocument()
    expect(modelMenuButton).toBeEnabled()
    await userEvent.click(modelMenuButton)
    await waitFor(() => expect(mockColumnClickHandlerProps.updateColumnWithModel).toHaveBeenCalled())
    await waitFor(() => expect(mockColumnClickHandlerProps.handleClose).toHaveBeenCalled())
  })
})
