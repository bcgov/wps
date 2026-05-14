import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { LocalizationProvider } from '@mui/x-date-pickers'
import { DateTime } from 'luxon'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SidePanel from './SidePanel'
import { ModelRunHour, ModelType } from '@/features/weatherToolkit/weatherToolkitTypes'

vi.mock('@/features/fba/components/ASADatePicker', () => ({
  default: ({ date, label }: { date: DateTime | null; label?: string }) => (
    <input aria-label={label ?? 'Date of Interest'} defaultValue={date?.toISODate() ?? ''} readOnly />
  )
}))

const MODEL_RUN_DATE = DateTime.fromISO('2026-04-15', { zone: 'utc' })

const defaultProps = {
  model: ModelType.GDPS,
  setModel: vi.fn(),
  modelRunDate: MODEL_RUN_DATE,
  setModelRunDate: vi.fn(),
  modelRunHour: ModelRunHour.ZERO,
  setModelRunHour: vi.fn()
}

const renderSidePanel = (props: Partial<typeof defaultProps> = {}) =>
  render(
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <SidePanel {...defaultProps} {...props} />
    </LocalizationProvider>
  )

describe('SidePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('static content', () => {
    it('renders the 4-Panel Charts heading', () => {
      renderSidePanel()
      expect(screen.getByText('4-Panel Charts')).toBeInTheDocument()
    })

    it('renders the Time section label', () => {
      renderSidePanel()
      expect(screen.getByText('Time')).toBeInTheDocument()
    })

    it('renders the Data Configuration section label', () => {
      renderSidePanel()
      expect(screen.getByText('Data Configuration')).toBeInTheDocument()
    })
  })

  describe('Model Run Date picker', () => {
    it('renders the date picker with label "Model Run Date (UTC)"', () => {
      renderSidePanel()
      expect(screen.getByLabelText(/model run date/i)).toBeInTheDocument()
    })

    it('passes the current modelRunDate to the date picker', () => {
      renderSidePanel()
      const input = screen.getByLabelText(/model run date/i) as HTMLInputElement
      expect(input.value).toContain('2026-04-15')
    })
  })

  describe('Model Run Hour select', () => {
    it('displays the current model run hour', () => {
      renderSidePanel({ modelRunHour: ModelRunHour.ZERO })
      expect(screen.getByRole('combobox', { name: /model run hour/i })).toHaveTextContent('00Z')
    })

    it('displays 12Z when modelRunHour is TWELVE', () => {
      renderSidePanel({ modelRunHour: ModelRunHour.TWELVE })
      expect(screen.getByRole('combobox', { name: /model run hour/i })).toHaveTextContent('12Z')
    })

    it('calls setModelRunHour with TWELVE when 12Z is selected', async () => {
      const setModelRunHour = vi.fn()
      renderSidePanel({ setModelRunHour })
      await userEvent.click(screen.getByRole('combobox', { name: /model run hour/i }))
      await userEvent.click(screen.getByRole('option', { name: '12Z' }))
      expect(setModelRunHour).toHaveBeenCalledWith(ModelRunHour.TWELVE)
    })

    it('calls setModelRunHour with ZERO when 00Z is selected', async () => {
      const setModelRunHour = vi.fn()
      renderSidePanel({ modelRunHour: ModelRunHour.TWELVE, setModelRunHour })
      await userEvent.click(screen.getByRole('combobox', { name: /model run hour/i }))
      await userEvent.click(screen.getByRole('option', { name: '00Z' }))
      expect(setModelRunHour).toHaveBeenCalledWith(ModelRunHour.ZERO)
    })
  })

  describe('Weather Model select', () => {
    it('displays the current weather model', () => {
      renderSidePanel({ model: ModelType.GDPS })
      expect(screen.getByRole('combobox', { name: /weather model/i })).toHaveTextContent('GDPS')
    })

    it('displays RDPS when model is RDPS', () => {
      renderSidePanel({ model: ModelType.RDPS })
      expect(screen.getByRole('combobox', { name: /weather model/i })).toHaveTextContent('RDPS')
    })

    it('calls setModel with RDPS when RDPS is selected', async () => {
      const setModel = vi.fn()
      renderSidePanel({ setModel })
      await userEvent.click(screen.getByRole('combobox', { name: /weather model/i }))
      await userEvent.click(screen.getByRole('option', { name: 'RDPS' }))
      expect(setModel).toHaveBeenCalledWith(ModelType.RDPS)
    })

    it('calls setModel with GDPS when GDPS is selected', async () => {
      const setModel = vi.fn()
      renderSidePanel({ model: ModelType.RDPS, setModel })
      await userEvent.click(screen.getByRole('combobox', { name: /weather model/i }))
      await userEvent.click(screen.getByRole('option', { name: 'GDPS' }))
      expect(setModel).toHaveBeenCalledWith(ModelType.GDPS)
    })
  })
})
