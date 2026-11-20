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
  it('selects an axis label and applies only after an explicit click', async () => {
    const onApply = vi.fn().mockReturnValue('Updated temperature forecasts for 2 days.')
    render(<ModelElevationComparisonPanel station={station} onClose={vi.fn()} onApply={onApply} />)
    const apply = screen.getByRole('button', { name: 'Apply to temperature forecasts' })
    expect(apply).toBeDisabled()
    expect(screen.getByRole('textbox', { name: 'Adjustment (°C)' })).toHaveAttribute('readonly')
    expect(screen.getByRole('textbox', { name: 'Adjustment (°C)' })).toHaveValue('Not set')
    const label = screen.getByRole('button', { name: 'HRDPS' })
    label.focus()
    await userEvent.keyboard('{Enter}')
    expect(label).toHaveAttribute('aria-pressed', 'true')
    await userEvent.click(screen.getByRole('button', { name: '9.8 °C/km' }))
    await userEvent.hover(screen.getByRole('button', { name: '9.8 °C/km' }))
    expect(await screen.findByRole('tooltip')).toHaveTextContent('Dry adiabatic')
    expect(onApply).not.toHaveBeenCalled()
    expect(screen.getByText('Temperature adjustment')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Adjustment (°C)' })).toHaveValue('-0.5')
    const rate = screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })
    await userEvent.clear(rate)
    expect(screen.getByRole('textbox', { name: 'Adjustment (°C)' })).toHaveValue('Not set')
    await userEvent.type(rate, '5')
    expect(screen.getByRole('textbox', { name: 'Adjustment (°C)' })).toHaveValue('-0.2')
    await userEvent.click(screen.getByRole('button', { name: '9.8 °C/km' }))
    await userEvent.click(apply)
    expect(onApply).toHaveBeenCalledWith('HRDPS', 9.8)
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
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
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
