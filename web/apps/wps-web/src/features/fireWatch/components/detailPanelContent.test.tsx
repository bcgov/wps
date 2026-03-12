import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

import { DateTime } from 'luxon'
import DetailPanelContent from '@/features/fireWatch/components/DetailPanelContent'
import { BurnStatusEnum, FuelTypeEnum, PrescriptionEnum } from '@/features/fireWatch/interfaces'
import { MUI_LICENSE } from '@/utils/env'
import { LicenseInfo } from '@mui/x-data-grid-pro'


const now = DateTime.now()
const mockFireWatch = {
  burnWindowEnd: now,
  burnWindowStart: now,
  contactEmail: ['test@gov.bc.ca'],
  fireCentre: {id: 1, name: 'test'},
  geometry: [123,123],
  station: {code: 1, name: 'test'},
  status: BurnStatusEnum.ACTIVE,
  title: 'test',
  // Fuel parameters
  fuelType: FuelTypeEnum.C1,
  percentConifer: undefined,
  percentDeadFir: undefined,
  percentGrassCuring: undefined,
  // Weather parameters
  tempMin: 1,
  tempPreferred: 2,
  tempMax: 3,
  rhMin: 1,
  rhPreferred: 2,
  rhMax: 3,
  windSpeedMin: 1,
  windSpeedPreferred: 2,
  windSpeedMax: 3,
  // FWI and FBP parameters
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
  id: 1,
  createTimestamp: now,
  createUser: 'test',
  updateTimestamp: now,
  updateUser: 'test'
}

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
  burnForecasts: [
    {
      id: 1,
      fireWatchId: 1,
      date: DateTime.fromISO('2024-05-01'),
      temp: 18.5,
      rh: 45,
      windSpeed: 10,
      ffmc: 85,
      dmc: 12,
      dc: 200,
      isi: 3,
      bui: 40,
      hfi: 100,
      inPrescription: PrescriptionEnum.ALL
    }
  ]
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
