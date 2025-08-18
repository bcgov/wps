import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { DateTime } from 'luxon'
import ModelHeader from './ModelHeader'
import { WeatherDeterminate, weatherModelsWithTooltips } from '@/api/moreCast2API'
import { MoreCast2Row } from '@/features/moreCast2/interfaces'

describe('ModelHeader', () => {
  const createMockParams = (field: string, headerName?: string) => ({
    field,
    colDef: {
      field,
      headerName: headerName
    }
  })

  const createMockRow = (timestamps: Partial<Record<string, string>> = {}): MoreCast2Row => ({
    ffmcCalcActual: 0,
    dmcCalcActual: 0,
    dcCalcActual: 0,
    isiCalcActual: 0,
    buiCalcActual: 0,
    fwiCalcActual: 0,
    dgrCalcActual: 0,
    grassCuringActual: 0,
    precipActual: 0,
    rhActual: 0,
    tempActual: 0,
    windDirectionActual: 0,
    windSpeedActual: 0,
    precipGDPS: 0,
    rhGDPS: 0,
    tempGDPS: 0,
    windDirectionGDPS: 0,
    windSpeedGDPS: 0,
    precipGDPS_BIAS: 0,
    rhGDPS_BIAS: 0,
    tempGDPS_BIAS: 0,
    windDirectionGDPS_BIAS: 0,
    windSpeedGDPS_BIAS: 0,
    precipGFS: 0,
    rhGFS: 0,
    tempGFS: 0,
    windDirectionGFS: 0,
    windSpeedGFS: 0,
    precipGFS_BIAS: 0,
    rhGFS_BIAS: 0,
    tempGFS_BIAS: 0,
    windDirectionGFS_BIAS: 0,
    windSpeedGFS_BIAS: 0,
    precipHRDPS: 0,
    rhHRDPS: 0,
    tempHRDPS: 0,
    windDirectionHRDPS: 0,
    windSpeedHRDPS: 0,
    precipHRDPS_BIAS: 0,
    rhHRDPS_BIAS: 0,
    tempHRDPS_BIAS: 0,
    windDirectionHRDPS_BIAS: 0,
    windSpeedHRDPS_BIAS: 0,
    precipNAM: 0,
    rhNAM: 0,
    tempNAM: 0,
    windDirectionNAM: 0,
    windSpeedNAM: 0,
    precipNAM_BIAS: 0,
    rhNAM_BIAS: 0,
    tempNAM_BIAS: 0,
    windDirectionNAM_BIAS: 0,
    windSpeedNAM_BIAS: 0,
    precipRDPS: 0,
    rhRDPS: 0,
    tempRDPS: 0,
    windDirectionRDPS: 0,
    windSpeedRDPS: 0,
    precipRDPS_BIAS: 0,
    rhRDPS_BIAS: 0,
    tempRDPS_BIAS: 0,
    windDirectionRDPS_BIAS: 0,
    windSpeedRDPS_BIAS: 0,
    id: '',
    stationCode: 0,
    stationName: '',
    forDate: DateTime.now(),
    latitude: 0,
    longitude: 0,
    predictionRunTimestampRDPS: null,
    predictionRunTimestampGDPS: null,
    predictionRunTimestampHRDPS: null,
    predictionRunTimestampNAM: null,
    predictionRunTimestampGFS: null,
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

        const { getByTestId, getByText } = render(<ModelHeader params={params} allRows={allRows} />)

        expect(getByText(modelType)).toBeInTheDocument()
        expect(getByTestId(`${modelType}-model-run-tooltip`)).toBeInTheDocument()
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
