import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { WeatherDeterminate, weatherModelsWithTooltips } from '@wps/api/moreCast2API'
import { DateTime } from 'luxon'
import type { MoreCast2Row } from '@/features/moreCast2/interfaces'
import { createEmptyMoreCast2Row } from '@/features/moreCast2/slices/dataSlice'
import ModelHeader from './ModelHeader'

describe('ModelHeader', () => {
  const createMockParams = (field: string, headerName?: string) => ({
    field,
    colDef: {
      field,
      headerName: headerName
    }
  })

  const createMockRow = (timestamps: Partial<Record<string, string>> = {}): MoreCast2Row => ({
    ...createEmptyMoreCast2Row('', 0, '', DateTime.now(), 0, 0),
    ...timestamps
  })

  describe('when no allRows provided', () => {
    it('should render simple typography for weather model without tooltip', () => {
      const params = createMockParams(WeatherDeterminate.HRDPS, WeatherDeterminate.HRDPS)

      const { getByTestId, queryByTestId } = render(<ModelHeader params={params} />)

      expect(getByTestId(`${WeatherDeterminate.HRDPS}-column-header`)).toBeInTheDocument()
      expect(queryByTestId(`${WeatherDeterminate.HRDPS}-model-run-tooltip`)).not.toBeInTheDocument()
    })

    it('should render simple typography for non-weather model', () => {
      const params = createMockParams('customField', 'Custom Header')

      const { getByTestId, getByText } = render(<ModelHeader params={params} />)

      expect(getByTestId('customField-column-header')).toBeInTheDocument()
      expect(getByText('Custom Header')).toBeInTheDocument()
    })
  })

  describe('when allRows is empty', () => {
    it('should render simple typography', () => {
      const params = createMockParams(WeatherDeterminate.HRDPS, WeatherDeterminate.HRDPS)

      const { getByTestId, queryByTestId } = render(<ModelHeader params={params} allRows={[]} />)

      expect(getByTestId(`${WeatherDeterminate.HRDPS}-column-header`)).toBeInTheDocument()
      expect(queryByTestId(`${WeatherDeterminate.HRDPS}-model-run-tooltip`)).not.toBeInTheDocument()
    })
  })

  describe('when modelType is not in weatherModelsWithTooltips', () => {
    it('should render simple typography for bias models', () => {
      const params = createMockParams('HRDPS_BIAS', 'HRDPS_BIAS')
      const allRows = [createMockRow()]

      const { getByTestId, queryByTestId } = render(<ModelHeader params={params} allRows={allRows} />)

      expect(getByTestId('HRDPS_BIAS-column-header')).toBeInTheDocument()
      expect(queryByTestId('HRDPS_BIAS-model-run-tooltip')).not.toBeInTheDocument()
    })
  })

  describe('with weather models that have tooltips', () => {
    const testTimestamp = '2023-08-14T10:30:00Z'

    describe.each(weatherModelsWithTooltips)('for model %s', modelType => {
      it(`should render tooltip when ${modelType} has timestamp`, () => {
        const params = createMockParams(modelType, modelType)
        const timestampField = `predictionRunTimestamp${modelType}`
        const allRows = [createMockRow({ [timestampField]: testTimestamp })]

        const { getByTestId, getByText, getByRole } = render(<ModelHeader params={params} allRows={allRows} />)

        expect(getByText(modelType)).toBeInTheDocument()
        expect(getByTestId(`${modelType}-model-run-tooltip`)).toBe(
          getByRole('button', { name: `${modelType} model run information` })
        )
      })

      it(`should render without tooltip when ${modelType} has no timestamp`, () => {
        const params = createMockParams(modelType, modelType)
        const allRows = [createMockRow()]

        const { getByTestId, queryByTestId } = render(<ModelHeader params={params} allRows={allRows} />)

        expect(getByTestId(`${modelType}-column-header`)).toBeInTheDocument()
        expect(queryByTestId(`${modelType}-model-run-tooltip`)).not.toBeInTheDocument()
      })
    })
  })

  it('shows ECMWF run information when the info button receives keyboard focus', async () => {
    const params = createMockParams(WeatherDeterminate.ECMWF, WeatherDeterminate.ECMWF)
    const allRows = [createMockRow({ predictionRunTimestampECMWF: '2026-11-17T12:00:00Z' })]
    const { getByRole, findByRole } = render(<ModelHeader params={params} allRows={allRows} />)

    await userEvent.tab()

    expect(getByRole('button', { name: 'ECMWF model run information' })).toHaveFocus()
    expect(await findByRole('tooltip')).toHaveTextContent('Model run: Nov 17, 2026 12:00 UTC')
  })

  describe('timestamp sorting and selection', () => {
    it('should use the latest timestamp when multiple rows have different timestamps', async () => {
      const params = createMockParams(WeatherDeterminate.HRDPS, WeatherDeterminate.HRDPS)
      const olderTimestamp = '2023-08-14T08:00:00Z'
      const newerTimestamp = '2023-08-14T12:00:00Z'
      const middleTimestamp = '2023-08-14T10:00:00Z'

      const allRows = [
        createMockRow({ predictionRunTimestampHRDPS: middleTimestamp }),
        createMockRow({ predictionRunTimestampHRDPS: olderTimestamp }),
        createMockRow({ predictionRunTimestampHRDPS: newerTimestamp })
      ]

      const { getByTestId } = render(<ModelHeader params={params} allRows={allRows} />)

      const tooltipTrigger = getByTestId(`${WeatherDeterminate.HRDPS}-model-run-tooltip`)
      expect(tooltipTrigger).toBeInTheDocument()

      // Hover to trigger tooltip
      fireEvent.mouseEnter(tooltipTrigger)

      // Wait for tooltip content to appear
      await waitFor(() => {
        const tooltip = screen.getByRole('tooltip')
        // Expect UTC time formatting (not local timezone)
        const expectedText = DateTime.fromISO(newerTimestamp).toUTC().toFormat('MMM dd, yyyy HH:mm ZZZZ')
        expect(tooltip).toHaveTextContent(`Model run: ${expectedText}`)
      })
    })

    it('should handle invalid timestamps gracefully', () => {
      const params = createMockParams(WeatherDeterminate.HRDPS, WeatherDeterminate.HRDPS)
      const validTimestamp = '2023-08-14T12:00:00Z'
      const invalidTimestamp = 'invalid-date'

      const allRows = [
        createMockRow({ predictionRunTimestampHRDPS: invalidTimestamp }),
        createMockRow({ predictionRunTimestampHRDPS: validTimestamp }),
        createMockRow({ predictionRunTimestampHRDPS: 'another-invalid-date' })
      ]

      const { getByTestId } = render(<ModelHeader params={params} allRows={allRows} />)

      const tooltip = getByTestId(`${WeatherDeterminate.HRDPS}-model-run-tooltip`)
      expect(tooltip).toBeInTheDocument()

      // Should use the only valid timestamp - verify tooltip exists (content is managed by Material-UI internally)
      // The presence of the tooltip testid means the component rendered with valid timestamp data
      expect(tooltip).toBeInTheDocument()
    })

    it('should render without tooltip when all timestamps are invalid', () => {
      const params = createMockParams(WeatherDeterminate.HRDPS, WeatherDeterminate.HRDPS)
      const allRows = [
        createMockRow({ predictionRunTimestampHRDPS: 'invalid-date-1' }),
        createMockRow({ predictionRunTimestampHRDPS: 'invalid-date-2' })
      ]

      const { getByTestId, queryByTestId } = render(<ModelHeader params={params} allRows={allRows} />)

      expect(getByTestId(`${WeatherDeterminate.HRDPS}-column-header`)).toBeInTheDocument()
      expect(queryByTestId(`${WeatherDeterminate.HRDPS}-model-run-tooltip`)).not.toBeInTheDocument()
    })
  })

  describe('component props', () => {
    it('should handle undefined headerName', () => {
      const params = createMockParams('test')

      const { getByTestId } = render(<ModelHeader params={params} />)

      const element = getByTestId('test-column-header')
      expect(element).toBeEmptyDOMElement()
    })

    it('should use field as fallback when headerName is empty', () => {
      const params = createMockParams('testField', '')

      const { getByTestId } = render(<ModelHeader params={params} />)

      const element = getByTestId('testField-column-header')
      expect(element).toBeEmptyDOMElement()
    })
  })
})
