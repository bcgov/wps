import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { vi } from 'vitest'
import type { ModelElevationRow } from '../modelElevation'
import ModelElevationComparisonPanel from './ModelElevationComparisonPanel'

const station: ModelElevationRow = {
  id: 'model-elevation-1',
  kind: 'modelElevation',
  stationCode: 1,
  stationName: 'Alpha station',
  stationElevation: 900,
  modelElevations: { HRDPS: 850.4, RDPS: 1150, GDPS: 900, ECMWF: 0, GFS: -20, NAM: 600, HRDPS_BIAS: 700 }
}

const model = (name: string): SVGElement => screen.getByRole('img').querySelector<SVGElement>(`[data-model="${name}"]`)!
const modelLabels = (name: string) => [
  ...Array.from(model(name).querySelectorAll('text'), node => node.textContent),
  name,
  screen.getByRole('button', { name }).nextElementSibling?.textContent
]

describe('model elevation comparison panel', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it.each(['', ' ', 'invalid', 'NaN', 'Infinity'])('ignores invalid saved rate %s', saved => {
    localStorage.setItem('morecastLastLapseRate', saved)
    render(<ModelElevationComparisonPanel station={station} onClose={vi.fn()} onApply={vi.fn()} />)
    expect(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })).toHaveValue(null)
  })

  it.each(['0.0', '-6.5', '9.8'])('prefills saved rate %s without selecting a model', saved => {
    localStorage.setItem('morecastLastLapseRate', saved)
    render(<ModelElevationComparisonPanel station={station} onClose={vi.fn()} onApply={vi.fn()} />)
    expect(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })).toHaveDisplayValue(saved)
    expect(screen.getByRole('button', { name: 'Fill temperature forecasts' })).toBeDisabled()
    expect(screen.queryByText('Preset lapse rates')).not.toBeInTheDocument()
  })

  it('saves a derived rate only on Fill and restores it when reopened', async () => {
    const props = { station, onClose: vi.fn(), onApply: vi.fn() }
    const { unmount } = render(<ModelElevationComparisonPanel {...props} />)
    await userEvent.click(screen.getByRole('button', { name: 'RDPS' }))
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Adjustment (°C)' }), '-2')
    expect(localStorage.getItem('morecastLastLapseRate')).toBeNull()
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(localStorage.getItem('morecastLastLapseRate')).toBe('-8.0')
    const rate = screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })
    await userEvent.clear(rate)
    await userEvent.type(rate, '5')
    await userEvent.tab()
    unmount()
    render(<ModelElevationComparisonPanel {...props} />)
    expect(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })).toHaveDisplayValue('-8.0')
  })

  it('does not overwrite a saved rate when applying an adjustment without elevations', async () => {
    localStorage.setItem('morecastLastLapseRate', '6.5')
    render(
      <ModelElevationComparisonPanel
        station={{ ...station, stationElevation: null }}
        onClose={vi.fn()}
        onApply={vi.fn()}
      />
    )
    await userEvent.click(screen.getByRole('button', { name: 'HRDPS' }))
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Adjustment (°C)' }), '2')
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(localStorage.getItem('morecastLastLapseRate')).toBe('6.5')
  })

  it('explains the date range in a tooltip even when Fill is disabled', async () => {
    render(<ModelElevationComparisonPanel station={station} onClose={vi.fn()} onApply={vi.fn()} />)
    const fill = screen.getByRole('button', { name: 'Fill temperature forecasts' })
    await userEvent.hover(fill.parentElement!)
    expect(await screen.findByRole('tooltip')).toHaveTextContent(
      'Fill temperature forecasts for this station in the selected date range.'
    )
  })

  it('rounds an entered adjustment on blur and applies the rounded value', async () => {
    const onApply = vi.fn()
    render(<ModelElevationComparisonPanel station={station} onClose={vi.fn()} onApply={onApply} />)
    await userEvent.click(screen.getByRole('button', { name: 'RDPS' }))
    const adjustment = screen.getByRole('spinbutton', { name: 'Adjustment (°C)' })
    await userEvent.type(adjustment, '-2.26')
    await userEvent.tab()
    expect(adjustment).toHaveDisplayValue('-2.3')
    expect(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })).toHaveValue(-9.2)
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(onApply).toHaveBeenCalledWith('RDPS', -2.3, false)
  })

  it('rounds an entered lapse rate on blur and uses it for the adjustment', async () => {
    const onApply = vi.fn()
    render(<ModelElevationComparisonPanel station={station} onClose={vi.fn()} onApply={onApply} />)
    await userEvent.click(screen.getByRole('button', { name: 'RDPS' }))
    const rate = screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })
    await userEvent.type(rate, '6.56')
    await userEvent.tab()
    expect(rate).toHaveValue(6.6)
    expect(rate).toHaveDisplayValue('6.6')
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(onApply).toHaveBeenCalledWith('RDPS', 1.6, false)
  })

  it.each([2, -2, 0])('preserves the rounded derived rate from adjustment %s', async value => {
    const onApply = vi.fn()
    render(
      <ModelElevationComparisonPanel
        station={{ ...station, modelElevations: { HRDPS: 1200, RDPS: 1900 } }}
        onClose={vi.fn()}
        onApply={onApply}
      />
    )
    await userEvent.click(screen.getByRole('button', { name: 'HRDPS' }))
    const adjustment = screen.getByRole('spinbutton', { name: 'Adjustment (°C)' })
    await userEvent.type(adjustment, String(value))
    await userEvent.click(screen.getByRole('button', { name: 'HRDPS' }))
    expect(adjustment).toHaveValue(value)
    await userEvent.click(screen.getByRole('button', { name: 'RDPS' }))
    const roundedRate = Number((value / 0.3).toFixed(1))
    expect(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })).toHaveValue(roundedRate)
    expect(onApply).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(onApply).toHaveBeenCalledWith('RDPS', roundedRate, false)
  })

  it('applies a direct adjustment without station or model elevations', async () => {
    const onApply = vi.fn()
    render(
      <ModelElevationComparisonPanel
        station={{ ...station, stationElevation: null, modelElevations: {} }}
        onClose={vi.fn()}
        onApply={onApply}
      />
    )
    await userEvent.click(screen.getByRole('button', { name: 'HRDPS' }))
    expect(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })).toBeDisabled()
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Adjustment (°C)' }), '2')
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(onApply).toHaveBeenCalledWith('HRDPS', 2, false)
    await userEvent.click(screen.getByRole('checkbox', { name: 'Overwrite existing forecasts' }))
    await userEvent.click(screen.getByRole('button', { name: 'RDPS' }))
    expect(screen.getByRole('spinbutton', { name: 'Adjustment (°C)' })).toHaveValue(null)
    expect(screen.getByRole('button', { name: 'Fill temperature forecasts' })).toBeDisabled()
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Adjustment (°C)' }), '3')
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(onApply).toHaveBeenLastCalledWith('RDPS', 3, true)
  })

  it('preserves the derived rate through equal and missing elevations and back', async () => {
    const onApply = vi.fn()
    render(
      <ModelElevationComparisonPanel
        station={{ ...station, modelElevations: { RDPS: 1150, GDPS: 900 } }}
        onClose={vi.fn()}
        onApply={onApply}
      />
    )
    const adjustment = screen.getByRole('spinbutton', { name: 'Adjustment (°C)' })
    const rate = screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })
    await userEvent.click(screen.getByRole('button', { name: 'RDPS' }))
    await userEvent.type(adjustment, '-2')
    expect(rate).toHaveValue(-8)
    await userEvent.click(screen.getByRole('button', { name: 'GDPS' }))
    expect(rate).toBeDisabled()
    expect(rate).toHaveValue(-8)
    expect(adjustment).toHaveValue(0)
    await userEvent.click(screen.getByRole('button', { name: 'HRDPS' }))
    expect(rate).toHaveValue(-8)
    expect(adjustment).toHaveValue(null)
    expect(screen.getByRole('button', { name: 'Fill temperature forecasts' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: 'RDPS' }))
    expect(rate).toHaveValue(-8)
    expect(adjustment).toHaveValue(-2)
    expect(onApply).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(onApply).toHaveBeenCalledWith('RDPS', -2, false)
    await userEvent.clear(adjustment)
    expect(screen.getByRole('button', { name: 'Fill temperature forecasts' })).toBeDisabled()
    await userEvent.type(adjustment, '0')
    expect(screen.getByRole('button', { name: 'Fill temperature forecasts' })).toBeEnabled()
  })

  it('selects an axis label and applies only after an explicit click', async () => {
    const onApply = vi.fn().mockReturnValue('Filled temperature forecasts for 2 days.')
    render(<ModelElevationComparisonPanel station={station} onClose={vi.fn()} onApply={onApply} />)
    const apply = screen.getByRole('button', { name: 'Fill temperature forecasts' })
    expect(apply).toBeDisabled()
    const adjustment = screen.getByRole('spinbutton', { name: 'Adjustment (°C)' })
    expect(adjustment).toHaveValue(null)
    const label = screen.getByRole('button', { name: 'HRDPS' })
    label.focus()
    await userEvent.keyboard('{Enter}')
    expect(label).toHaveAttribute('aria-pressed', 'true')
    await userEvent.clear(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' }))
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' }), '9.8')
    expect(onApply).not.toHaveBeenCalled()
    expect(screen.getByText('Temperature adjustment')).toBeInTheDocument()
    expect(adjustment).toHaveValue(-0.5)
    const rate = screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })
    await userEvent.clear(rate)
    expect(adjustment).toHaveValue(null)
    await userEvent.type(rate, '5')
    expect(adjustment).toHaveValue(-0.2)
    await userEvent.click(screen.getByRole('button', { name: 'RDPS' }))
    expect(adjustment).toHaveValue(1.3)
    await userEvent.click(screen.getByRole('button', { name: 'GDPS' }))
    expect(adjustment).toHaveValue(0)
    await userEvent.click(screen.getByRole('button', { name: 'HRDPS' }))
    await userEvent.clear(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' }))
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' }), '9.8')
    await userEvent.click(apply)
    expect(onApply.mock.calls[0][0]).toBe('HRDPS')
    expect(onApply.mock.calls[0][1]).toBe(-0.5)
    expect(screen.getByRole('status')).toHaveTextContent('2 days')
  })

  it('shows raw models in grid order with elevations and signed differences', () => {
    render(<ModelElevationComparisonPanel station={station} onClose={vi.fn()} />)
    expect(screen.getByRole('region', { name: 'Model elevations for Alpha station' })).toBeInTheDocument()
    expect(screen.getByText('Station elevation: 900 m')).toBeInTheDocument()
    expect(
      [...screen.getByRole('img').querySelectorAll('[data-model]')].map(node => node.getAttribute('data-model'))
    ).toEqual(['HRDPS', 'RDPS', 'GDPS', 'ECMWF', 'GFS'])
    expect(modelLabels('HRDPS')).toEqual(['850 m', 'HRDPS', '-50 m'])
    expect(modelLabels('RDPS')).toEqual(['1,150 m', 'RDPS', '+250 m'])
    expect(modelLabels('GDPS')).toEqual(['900 m', 'GDPS', '0 m'])
    expect(modelLabels('ECMWF')).toEqual(['0 m', 'ECMWF', '-900 m'])
    expect(modelLabels('GFS')).toEqual(['-20 m', 'GFS', '-920 m'])
    expect(screen.getByLabelText('Station elevation 900 m')).toBeInTheDocument()
  })

  it('calculates differences before rounding displayed elevations', () => {
    render(
      <ModelElevationComparisonPanel
        station={{ ...station, stationElevation: 1000.49, modelElevations: { HRDPS: 1000.51 } }}
        onClose={vi.fn()}
      />
    )
    expect(modelLabels('HRDPS')).toEqual(['1,001 m', 'HRDPS', '0 m'])
  })

  it('leaves unavailable models unplotted and keeps zero as an elevation', () => {
    render(
      <ModelElevationComparisonPanel
        station={{
          ...station,
          stationElevation: 0,
          modelElevations: { HRDPS: 0, RDPS: null, ECMWF: Number.NaN, GFS: Number.POSITIVE_INFINITY }
        }}
        onClose={vi.fn()}
      />
    )
    expect(model('HRDPS').querySelector('circle')).toBeInTheDocument()
    expect(modelLabels('HRDPS')).toEqual(['0 m', 'HRDPS', '0 m'])
    for (const name of ['RDPS', 'GDPS', 'ECMWF', 'GFS']) {
      expect(modelLabels(name)).toEqual([name, 'N/A'])
      expect(model(name).querySelector('circle')).toBeNull()
    }
  })

  it('uses a valid scale when every model has the station elevation', () => {
    render(
      <ModelElevationComparisonPanel
        station={{ ...station, modelElevations: { HRDPS: 900, RDPS: 900, GDPS: 900, ECMWF: 900, GFS: 900 } }}
        onClose={vi.fn()}
      />
    )
    const markers = [...screen.getByRole('img').querySelectorAll('circle')]
    expect(markers).toHaveLength(5)
    const positions = markers.map(marker => Number(marker.getAttribute('cy')))
    expect(new Set(positions).size).toBe(1)
    expect(positions.every(y => Number.isFinite(y) && y > 0 && y < 250)).toBe(true)
    expect(screen.getByRole('img').querySelector('polyline, path')).toBeNull()
  })

  it('shows model elevations without differences when station elevation is unavailable', () => {
    render(<ModelElevationComparisonPanel station={{ ...station, stationElevation: null }} onClose={vi.fn()} />)
    expect(modelLabels('HRDPS')).toEqual(['850 m', 'HRDPS', ''])
    expect(screen.getByText('Station elevation unavailable. Differences cannot be calculated.')).toBeInTheDocument()
    expect(screen.getByRole('img').querySelector('line[stroke-dasharray]')).toBeNull()
  })

  it('shows an empty message when only bias or retired models have elevations', () => {
    render(
      <ModelElevationComparisonPanel
        station={{ ...station, modelElevations: { NAM: 600, HRDPS_BIAS: 700 } }}
        onClose={vi.fn()}
      />
    )
    expect(screen.getByText('Model elevations are not available for this station.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'HRDPS' })).toBeEnabled()
  })

  it('requests dismissal with the Close button', async () => {
    const onClose = vi.fn()
    render(<ModelElevationComparisonPanel station={station} onClose={onClose} />)
    await userEvent.click(screen.getByRole('button', { name: 'Close elevation comparison' }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not mount the chart when closed', () => {
    render(<ModelElevationComparisonPanel station={null} onClose={vi.fn()} />)
    expect(screen.queryByRole('region')).not.toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })
})
