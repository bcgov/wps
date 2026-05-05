import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

import { DateTime } from 'luxon'
import DetailPanelContent from '@/features/fireWatch/components/DetailPanelContent'
import { FuelTypeEnum, BurnStatusEnum, PrescriptionEnum } from '@/features/fireWatch/interfaces'
import { MUI_LICENSE } from '@wps/utils/env'
import { LicenseInfo } from '@mui/x-license'
import { createMockBurnForecast, createMockFireWatch } from './fireWatchTestUtils'

const mockFireWatch = createMockFireWatch()

const mockRowWithData = {
  id: 1,
  title: 'test',
  fireCentre: 'test',
  station: 'test',
  fuelType: FuelTypeEnum.C1,
  status: BurnStatusEnum.ACTIVE,
  burnWindowStart: DateTime.now(),
  burnWindowEnd: DateTime.now(),
  inPrescription: PrescriptionEnum.ALL,
  fireWatch: mockFireWatch,
  burnForecasts: [createMockBurnForecast()]
}

const mockRowWithoutData = {
  id: 2,
  title: 'test',
  fireCentre: 'test',
  station: 'test',
  fuelType: FuelTypeEnum.C1,
  status: BurnStatusEnum.ACTIVE,
  burnWindowStart: DateTime.now(),
  burnWindowEnd: DateTime.now(),
  inPrescription: PrescriptionEnum.ALL,
  fireWatch: mockFireWatch,
  burnForecasts: []
}

describe('DetailPanelContent', () => {
  beforeEach(() => LicenseInfo.setLicenseKey(MUI_LICENSE))
  it('renders DataGridPro with data', () => {
    render(<DetailPanelContent row={mockRowWithData} />)

    const grid = screen.getByTestId('detail-panel-content-1')
    expect(grid).toBeInTheDocument()
    expect(screen.queryByText('No data available.')).not.toBeInTheDocument()

    // Check that formatted values are rendered correctly
    expect(screen.getByText('2024-05-01')).toBeInTheDocument()
    expect(screen.getByText('18.5')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument()
  })

  it('renders "No data available" when forecasts are empty', () => {
    render(<DetailPanelContent row={mockRowWithoutData} />)

    expect(screen.getByText('No data available.')).toBeInTheDocument()
    expect(screen.queryByTestId('detail-panel-content-1')).not.toBeInTheDocument()
  })

  it('applies the correct row class based on inPrescription field', () => {
    render(<DetailPanelContent row={mockRowWithData} />)

    const row = screen.getByRole('row', { name: /2024-05-01/i })
    expect(row.className).toMatch(/in-prescription-all/)
  })

  it('formats numbers correctly in the grid', () => {
    render(<DetailPanelContent row={mockRowWithData} />)

    // Should display formatted number with 1 decimal place for temp
    expect(screen.getByText('18.5')).toBeInTheDocument()

    // Should display whole numbers for other columns
    expect(screen.getByText('3')).toBeInTheDocument() // windSpeed
    expect(screen.getByText('85')).toBeInTheDocument() // ffmc
  })
})
