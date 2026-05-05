import FireWatchDashboard from '@/features/fireWatch/components/FireWatchDashboard'
import { FireWatchDetailsModalProps } from '@/features/fireWatch/components/FireWatchDetailsModal'
import { PrescriptionEnum } from '@/features/fireWatch/interfaces'
import burnForecastSlice, { initialState } from '@/features/fireWatch/slices/burnForecastSlice'
import { createTestStore } from '@/test/testUtils'
import { MUI_LICENSE } from '@wps/utils/env'
import { LicenseInfo } from '@mui/x-license'
import { combineReducers } from '@reduxjs/toolkit'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as burnForecastSliceModule from '@/features/fireWatch/slices/burnForecastSlice'
import userEvent from '@testing-library/user-event'
import { createMockBurnForecast, createMockFireWatch } from './fireWatchTestUtils'

const burnForecastsReducer = combineReducers({ burnForecasts: burnForecastSlice })

vi.mock('features/fireWatch/fireWatchApi', () => ({
  getBurnForecasts: () => mockFireWatchBurnForecasts
}))

vi.mock('@/features/fireWatch/components/FireWatchDetailsModal', () => {
  return {
    default: ({ open }: FireWatchDetailsModalProps) => (open ? <div>FireWatch Modal Open</div> : <div></div>)
  }
})

vi.mock('@/features/fireWatch/components/DetailPanelContent', () => ({
  __esModule: true,
  default: ({ row }: any) => <div data-testid="detail-panel">Detail: {row.title}</div>
}))

describe('FireWatchDashboard', async () => {
  let testStore: ReturnType<typeof createTestStore>
  beforeEach(() => {
    LicenseInfo.setLicenseKey(MUI_LICENSE)
    testStore = createTestStore({ burnForecasts: { ...initialState } }, burnForecastsReducer)
  })

  const renderDashboard = () =>
    render(
      <Provider store={testStore}>
        <FireWatchDashboard />
      </Provider>
    )

  it('dispatches fetchBurnForecasts on mount', async () => {
    const dispatchSpy = vi.spyOn(testStore, 'dispatch')
    renderDashboard()

    await waitFor(() => {
      expect(dispatchSpy).toHaveBeenCalled()
    })
  })

  it('should render', async () => {
    renderDashboard()

    await waitFor(() => {
      const dashboard = screen.getByTestId('fire-watch-dashboard')
      expect(dashboard).toBeInTheDocument()
    })
  })

  it('renders the grid with rows', async () => {
    await act(async () => renderDashboard())

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    // Check if FireWatch titles are rendered
    expect(screen.getByText('test-1')).toBeInTheDocument()
    expect(screen.getByText('test-2')).toBeInTheDocument()
    expect(screen.getByText('test-3')).toBeInTheDocument()
  })

  it('opens modal when info icon is clicked', async () => {
    await act(async () => renderDashboard())

    const infoButton = screen.getAllByLabelText('View details')[0]
    fireEvent.click(infoButton)

    await waitFor(() => {
      expect(screen.getByText('FireWatch Modal Open')).toBeInTheDocument()
    })
  })

  it('renders the detail panel when expanded', async () => {
    await act(async () => renderDashboard())

    const expandButton = screen.getAllByLabelText('Expand')[0]
    fireEvent.click(expandButton)

    await waitFor(() => {
      expect(screen.getByTestId('detail-panel')).toBeInTheDocument()
    })
  })
  it('applies correct row class based on inPrescription value', async () => {
    await act(async () => renderDashboard())

    const row1 = document.querySelector('[data-id="1"]')
    expect(row1).toBeInTheDocument()
    expect(row1).toHaveClass('in-prescription-all')

    const row2 = document.querySelector('[data-id="2"]')
    expect(row2).toBeInTheDocument()
    expect(row2).toHaveClass('in-prescription-hfi')

    const row3 = document.querySelector('[data-id="3"]')
    expect(row3).toBeInTheDocument()
    expect(row3).toHaveClass('in-prescription-no')
  })

  it('shows error snackbar when processRowUpdate fails', async () => {
    const user = userEvent.setup()
    vi.spyOn(burnForecastSliceModule, 'updateFireWatch').mockImplementation(() => async () => {
      throw new Error('Update failed')
    })

    await act(async () => renderDashboard())

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('test-1')).toBeInTheDocument()

    // find the status cell for the first row and simulate editing
    const statusCells = document.querySelectorAll('.editable-status-cell')
    expect(statusCells.length).toBeGreaterThan(0)
    await user.dblClick(statusCells[0])

    // select a new status from dropdown (simulate status change)
    await user.click(screen.getByText('Complete', { selector: 'li' }))
    await user.click(document.body) // click outside to trigger update

    // wait for error snackbar to appear
    const alert = await screen.findByTestId('snackbar-alert')
    expect(alert).toHaveTextContent('Failed to update row status')
  })

  it('updates the status with a dropdown', async () => {
    const user = userEvent.setup()
    vi.spyOn(burnForecastSliceModule, 'updateFireWatch').mockImplementation(() => async () => {
      return mockFireWatchBurnForecasts[0]
    })

    await act(async () => renderDashboard())

    const statusCells = document.querySelectorAll('.editable-status-cell')
    expect(statusCells.length).toBeGreaterThan(0)
    expect(statusCells[0].querySelector('[data-testid="active-icon"]')).toBeInTheDocument()
    await user.dblClick(statusCells[0])

    // select a new status from dropdown (simulate status change)
    await user.click(screen.getByText('Complete', { selector: 'li' }))
    await user.click(document.body) // click outside to trigger update
    expect(statusCells[0].textContent).toContain('Complete')
    expect(statusCells[0].querySelector('[data-testid="complete-icon"]')).toBeInTheDocument()

    // select a new status from dropdown
    await user.dblClick(statusCells[1])
    await user.click(screen.getByText('Hold', { selector: 'li' }))
    await user.click(document.body) // click outside to trigger update
    expect(statusCells[1].textContent).toContain('Hold')
    expect(statusCells[1].querySelector('[data-testid="hold-icon"]')).toBeInTheDocument()

    // wait for error snackbar to appear
    const alert = screen.queryByTestId('snackbar-alert')
    expect(alert).not.toBeInTheDocument()
  })
})

const mockFireWatchBurnForecasts = [
  {
    fireWatch: createMockFireWatch({ id: 1, title: 'test-1' }),
    burnForecasts: [createMockBurnForecast({ inPrescription: PrescriptionEnum.ALL })]
  },
  {
    fireWatch: createMockFireWatch({ id: 2, title: 'test-2' }),
    burnForecasts: [createMockBurnForecast({ inPrescription: PrescriptionEnum.HFI })]
  },
  {
    fireWatch: createMockFireWatch({ id: 3, title: 'test-3' }),
    burnForecasts: [createMockBurnForecast({ inPrescription: PrescriptionEnum.NO })]
  }
]
