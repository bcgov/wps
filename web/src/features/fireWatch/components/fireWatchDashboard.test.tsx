import FireWatchDashboard from '@/features/fireWatch/components/FireWatchDashboard'
import { FireWatchDetailsModalProps } from '@/features/fireWatch/components/FireWatchDetailsModal'
import { BurnStatusEnum, FireWatch, FuelTypeEnum, PrescriptionEnum } from '@/features/fireWatch/interfaces'
import burnForecastSlice, { BurnForecastsState, initialState } from '@/features/fireWatch/slices/burnForecastSlice'
import { MUI_LICENSE } from '@/utils/env'
import { LicenseInfo } from '@mui/x-data-grid-pro'
import { combineReducers, configureStore } from '@reduxjs/toolkit'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as burnForecastSliceModule from '@/features/fireWatch/slices/burnForecastSlice'
import userEvent from '@testing-library/user-event'

const buildTestStore = (initialState: BurnForecastsState) => {
  const rootReducer = combineReducers({ burnForecasts: burnForecastSlice })
  const testStore = configureStore({
    reducer: rootReducer,
    preloadedState: {
      burnForecasts: initialState
    }
  })
  return testStore
}

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
  beforeEach(() => LicenseInfo.setLicenseKey(MUI_LICENSE))

  it('dispatches fetchBurnForecasts on mount', () => {
    const testStore = buildTestStore({
      ...initialState
    })
    const dispatchSpy = vi.spyOn(testStore, 'dispatch')
    render(
      <Provider store={testStore}>
        <FireWatchDashboard />
      </Provider>
    )
    expect(dispatchSpy).toHaveBeenCalled()
  })

  it('should render', async () => {
    const testStore = buildTestStore({
      ...initialState
    })
    render(
      <Provider store={testStore}>
        <FireWatchDashboard />
      </Provider>
    )

    const dashboard = screen.getByTestId('fire-watch-dashboard')
    expect(dashboard).toBeInTheDocument()
  })

  it('renders the grid with rows', async () => {
    const testStore = buildTestStore({
      ...initialState
    })
    await act(async () =>
      render(
        <Provider store={testStore}>
          <FireWatchDashboard />
        </Provider>
      )
    )

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    // Check if FireWatch titles are rendered
    expect(screen.getByText('test-1')).toBeInTheDocument()
    expect(screen.getByText('test-2')).toBeInTheDocument()
    expect(screen.getByText('test-3')).toBeInTheDocument()
  })

  it('opens modal when info icon is clicked', async () => {
    const testStore = buildTestStore({
      ...initialState
    })
    await act(async () =>
      render(
        <Provider store={testStore}>
          <FireWatchDashboard />
        </Provider>
      )
    )
    const infoButton = screen.getAllByLabelText('View details')[0]
    fireEvent.click(infoButton)

    await waitFor(() => {
      expect(screen.getByText('FireWatch Modal Open')).toBeInTheDocument()
    })
  })

  it('renders the detail panel when expanded', async () => {
    const testStore = buildTestStore({
      ...initialState
    })
    await act(async () =>
      render(
        <Provider store={testStore}>
          <FireWatchDashboard />
        </Provider>
      )
    )
    const expandButton = screen.getAllByLabelText('Expand')[0]
    fireEvent.click(expandButton)

    await waitFor(() => {
      expect(screen.getByTestId('detail-panel')).toBeInTheDocument()
    })
  })
  it('applies correct row class based on inPrescription value', async () => {
    const testStore = buildTestStore({
      ...initialState
    })
    await act(async () =>
      render(
        <Provider store={testStore}>
          <FireWatchDashboard />
        </Provider>
      )
    )

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

    const testStore = buildTestStore({
      ...initialState
    })

    await act(async () =>
      render(
        <Provider store={testStore}>
          <FireWatchDashboard />
        </Provider>
      )
    )

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

    const testStore = buildTestStore({
      ...initialState
    })

    await act(async () =>
      render(
        <Provider store={testStore}>
          <FireWatchDashboard />
        </Provider>
      )
    )

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('test-1')).toBeInTheDocument()

    // find the status cell for the first row and simulate editing
    const statusCells = document.querySelectorAll('.editable-status-cell')
    expect(statusCells.length).toBeGreaterThan(0)
    await user.dblClick(statusCells[0])

    // select a new status from dropdown (simulate status change)
    await user.click(screen.getByText('Complete', { selector: 'li' }))
    await user.click(document.body) // click outside to trigger update
    expect(statusCells[0].textContent).toContain('Complete')

    // select a new status from dropdown (simulate status change)
    await user.dblClick(statusCells[1])
    await user.click(screen.getByText('Hold', { selector: 'li' }))
    await user.click(document.body) // click outside to trigger update
    expect(statusCells[1].textContent).toContain('Hold')

    // wait for error snackbar to appear
    const alert = screen.queryByTestId('snackbar-alert')
    expect(alert).not.toBeInTheDocument()
  })
})

export const getMockFireWatch = (id: number, title: string): FireWatch => {
  const now = DateTime.now()
  return {
    id,
    title,
    burnWindowEnd: now,
    burnWindowStart: now,
    contactEmail: ['test@example.com'],
    fireCentre: {
      id: 1,
      name: 'fire-centre-test'
    },
    geometry: [1, 2],
    station: {
      code: 1,
      name: 'test'
    },
    status: BurnStatusEnum.ACTIVE,
    fuelType: FuelTypeEnum.C2,
    tempMin: 1,
    tempPreferred: 2,
    tempMax: 3,
    rhMin: 1,
    rhPreferred: 2,
    rhMax: 3,
    windSpeedMin: 1,
    windSpeedPreferred: 2,
    windSpeedMax: 3,
    ffmcMin: 1,
    ffmcPreferred: 2,
    ffmcMax: 3,
    dmcMin: 1,
    dmcPreferred: 2,
    dmcMax: 3,
    dcMin: 1,
    dcPreferred: 2,
    dcMax: 3,
    isiMin: 1,
    isiPreferred: 2,
    isiMax: 3,
    buiMin: 1,
    buiPreferred: 2,
    buiMax: 3,
    hfiMin: 1,
    hfiPreferred: 2,
    hfiMax: 3,
    createTimestamp: now,
    createUser: 'test',
    updateTimestamp: now,
    updateUser: 'test'
  }
}

const getMockBurnForecast = (id: number, inPrescription: PrescriptionEnum) => {
  return {
    id,
    inPrescription,
    fireWatchId: 1,
    date: DateTime.now(),
    temp: 2,
    rh: 2,
    windSpeed: 2,
    ffmc: 2,
    dmc: 2,
    dc: 2,
    isi: 2,
    bui: 2,
    hfi: 2,
    status: BurnStatusEnum.ACTIVE
  }
}

const mockFireWatchBurnForecasts = [
  {
    fireWatch: getMockFireWatch(1, 'test-1'),
    burnForecasts: [getMockBurnForecast(1, PrescriptionEnum.ALL)]
  },
  {
    fireWatch: getMockFireWatch(2, 'test-2'),
    burnForecasts: [getMockBurnForecast(1, PrescriptionEnum.HFI)]
  },
  {
    fireWatch: getMockFireWatch(3, 'test-3'),
    burnForecasts: [getMockBurnForecast(1, PrescriptionEnum.NO)]
  }
]
