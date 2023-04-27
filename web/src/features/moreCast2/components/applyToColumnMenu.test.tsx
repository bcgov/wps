import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DEFAULT_MODEL_TYPE } from 'api/moreCast2API'
import ApplyToColumnMenu from 'features/moreCast2/components/ApplyToColumnMenu'
import { ColumnDefBuilder } from 'features/moreCast2/components/ColumnDefBuilder'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'
import React from 'react'

describe('ApplyToColumnMenu', () => {
  it('should not render the menu when no context from a click exists', async () => {
    const mockUpdateColumnWithModel = jest.fn()
    const mockHandleClose = jest.fn()

    const { queryByText } = render(
      <ApplyToColumnMenu
        colDef={null}
        contextMenu={null}
        updateColumnWithModel={mockUpdateColumnWithModel}
        handleClose={mockHandleClose}
      />
    )
    const menu = queryByText('Apply')
    expect(menu).not.toBeInTheDocument()
  })

  it('should render the menu when context from a click exists', async () => {
    const mockUpdateColumnWithModel = jest.fn()
    const mockHandleClose = jest.fn()

    const { getByTestId } = render(
      <ApplyToColumnMenu
        colDef={null}
        contextMenu={{ mouseX: 1, mouseY: 1 }}
        updateColumnWithModel={mockUpdateColumnWithModel}
        handleClose={mockHandleClose}
      />
    )
    const menu = getByTestId('apply-to-column-menu')
    expect(menu).toBeInTheDocument()
  })

  it('should render the menu when context from a click exists', async () => {
    const mockUpdateColumnWithModel = jest.fn()
    const mockHandleClose = jest.fn()

    const { getByTestId } = render(
      <ApplyToColumnMenu
        colDef={null}
        contextMenu={{ mouseX: 1, mouseY: 1 }}
        updateColumnWithModel={mockUpdateColumnWithModel}
        handleClose={mockHandleClose}
      />
    )
    const menu = getByTestId('apply-to-column-menu')
    expect(menu).toBeInTheDocument()
  })

  describe('clicking apply', () => {
    const colDefBuilder = new ColumnDefBuilder('testField', 'testHeader', 'number', 1, new GridComponentRenderer())
    const colDef = colDefBuilder.generateColDef()

    it('should apply the model to the supplied column definition', async () => {
      const mockUpdateColumnWithModel = jest.fn()
      const mockHandleClose = jest.fn()

      const { getByTestId } = render(
        <ApplyToColumnMenu
          colDef={colDef}
          contextMenu={{ mouseX: 1, mouseY: 1 }}
          updateColumnWithModel={mockUpdateColumnWithModel}
          handleClose={mockHandleClose}
        />
      )
      const applyButton = getByTestId('apply-model-to-column-button')
      expect(applyButton).toBeInTheDocument()

      await userEvent.click(applyButton)
      await waitFor(() => expect(mockUpdateColumnWithModel).toBeCalledTimes(1))
      await waitFor(() => expect(mockHandleClose).toBeCalledTimes(1))
      await waitFor(() => expect(mockUpdateColumnWithModel).toBeCalledWith(DEFAULT_MODEL_TYPE, colDef))
    })

    it('should not attempt to apply the model to a column definition if its null', async () => {
      const mockUpdateColumnWithModel = jest.fn()
      const mockHandleClose = jest.fn()

      const { getByTestId } = render(
        <ApplyToColumnMenu
          colDef={null}
          contextMenu={{ mouseX: 1, mouseY: 1 }}
          updateColumnWithModel={mockUpdateColumnWithModel}
          handleClose={mockHandleClose}
        />
      )
      const applyButton = getByTestId('apply-model-to-column-button')
      expect(applyButton).toBeInTheDocument()

      await userEvent.click(applyButton)
      await waitFor(() => expect(mockUpdateColumnWithModel).not.toBeCalled())
      await waitFor(() => expect(mockHandleClose).not.toBeCalled())
    })
  })
})
