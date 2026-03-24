import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import RasterTypeDropdown from './RasterTypeDropdown'

describe('RasterTypeDropdown', () => {
  const mockSetSelectedRasterType = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all raster type options', () => {
    render(<RasterTypeDropdown selectedRasterType="fwi" setSelectedRasterType={mockSetSelectedRasterType} />)

    const dropdown = screen.getByLabelText('Raster Type')
    expect(dropdown).toBeInTheDocument()
  })

  it('disables fire weather options when rasterDataAvailable is false', () => {
    render(
      <RasterTypeDropdown
        selectedRasterType="fuel"
        setSelectedRasterType={mockSetSelectedRasterType}
        rasterDataAvailable={false}
      />
    )

    // Open the dropdown
    const dropdown = screen.getByRole('combobox')
    fireEvent.mouseDown(dropdown)

    // Check that fuel is enabled
    const fuelOption = screen.getByRole('option', { name: 'Fuel' })
    expect(fuelOption).not.toHaveAttribute('aria-disabled', 'true')

    // Check that FWI is disabled
    const fwiOption = screen.getByRole('option', { name: 'FWI' })
    expect(fwiOption).toHaveAttribute('aria-disabled', 'true')

    // Check that BUI is disabled
    const buiOption = screen.getByRole('option', { name: 'BUI' })
    expect(buiOption).toHaveAttribute('aria-disabled', 'true')
  })

  it('enables all options when rasterDataAvailable is true', () => {
    render(
      <RasterTypeDropdown
        selectedRasterType="fwi"
        setSelectedRasterType={mockSetSelectedRasterType}
        rasterDataAvailable={true}
      />
    )

    // Open the dropdown
    const dropdown = screen.getByRole('combobox')
    fireEvent.mouseDown(dropdown)

    // Check that all options are enabled
    const fuelOption = screen.getByRole('option', { name: 'Fuel' })
    expect(fuelOption).not.toHaveAttribute('aria-disabled', 'true')

    const fwiOption = screen.getByRole('option', { name: 'FWI' })
    expect(fwiOption).not.toHaveAttribute('aria-disabled', 'true')

    const buiOption = screen.getByRole('option', { name: 'BUI' })
    expect(buiOption).not.toHaveAttribute('aria-disabled', 'true')
  })

  it('defaults rasterDataAvailable to true when not provided', () => {
    render(<RasterTypeDropdown selectedRasterType="fwi" setSelectedRasterType={mockSetSelectedRasterType} />)

    const dropdown = screen.getByRole('combobox')
    fireEvent.mouseDown(dropdown)

    // All options should be enabled by default
    const fwiOption = screen.getByRole('option', { name: 'FWI' })
    expect(fwiOption).not.toHaveAttribute('aria-disabled', 'true')
  })

  it('prevents selection of disabled fire weather options when data unavailable', () => {
    render(
      <RasterTypeDropdown
        selectedRasterType="fuel"
        setSelectedRasterType={mockSetSelectedRasterType}
        rasterDataAvailable={false}
      />
    )

    // Open the dropdown
    const dropdown = screen.getByRole('combobox')
    fireEvent.mouseDown(dropdown)

    // Try to click a disabled option (FWI)
    const fwiOption = screen.getByRole('option', { name: 'FWI' })
    fireEvent.click(fwiOption)

    // Callback should not have been called
    expect(mockSetSelectedRasterType).not.toHaveBeenCalled()
  })

  it('allows selection of fuel when data unavailable', () => {
    render(
      <RasterTypeDropdown
        selectedRasterType="fwi"
        setSelectedRasterType={mockSetSelectedRasterType}
        rasterDataAvailable={false}
      />
    )

    // Open the dropdown
    const dropdown = screen.getByRole('combobox')
    fireEvent.mouseDown(dropdown)

    // Click fuel option
    const fuelOption = screen.getByRole('option', { name: 'Fuel' })
    fireEvent.click(fuelOption)

    // Callback should have been called with 'fuel'
    expect(mockSetSelectedRasterType).toHaveBeenCalledWith('fuel')
  })
})
