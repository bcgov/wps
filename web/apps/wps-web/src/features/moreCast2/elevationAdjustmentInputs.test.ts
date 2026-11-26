import { calculateElevationAdjustmentInputs, formatElevationAdjustmentInput } from './elevationAdjustmentInputs'

const rateInput = (value: string) => ({ field: 'rate' as const, value })
const adjustmentInput = (value: string) => ({ field: 'adjustment' as const, value })

describe('elevation adjustment inputs', () => {
  it('rounds the rate before applying it and leaves manual rates unrestricted', () => {
    expect(calculateElevationAdjustmentInputs(rateInput('6.56'), 0.25)).toEqual({
      rate: 6.6,
      adjustment: 1.6,
      canConvert: true
    })
    expect(calculateElevationAdjustmentInputs(rateInput('-20'), 0.5).adjustment).toBe(-10)
  })
  it('rounds a direct adjustment before deriving the rate', () => {
    expect(calculateElevationAdjustmentInputs(adjustmentInput('-2.26'), 0.25)).toEqual({
      rate: -9.2,
      adjustment: -2.3,
      canConvert: true
    })
  })
  it.each(['', ' ', 'invalid', 'Infinity', 'NaN'])('leaves invalid input %s blank', value => {
    expect(calculateElevationAdjustmentInputs(rateInput(value), 0.25)).toEqual({
      rate: null,
      adjustment: null,
      canConvert: true
    })
  })
  it('keeps zero as a valid rate and adjustment', () => {
    expect(calculateElevationAdjustmentInputs(rateInput('0'), 0.5).adjustment).toBe(0)
    expect(calculateElevationAdjustmentInputs(adjustmentInput('0'), 0.5).rate).toBe(0)
  })
  it.each([null, 0])('allows a direct adjustment without convertible elevations %s', difference => {
    expect(calculateElevationAdjustmentInputs(adjustmentInput('2'), difference)).toEqual({
      rate: null,
      adjustment: 2,
      canConvert: false
    })
  })
  it('retains a rate through missing and equal elevations', () => {
    expect(calculateElevationAdjustmentInputs(rateInput('6.5'), null)).toEqual({
      rate: 6.5,
      adjustment: null,
      canConvert: false
    })
    expect(calculateElevationAdjustmentInputs(rateInput('6.5'), 0)).toEqual({
      rate: 6.5,
      adjustment: 0,
      canConvert: false
    })
  })
  it('preserves typed text and formats only the inactive input', () => {
    expect(formatElevationAdjustmentInput(rateInput('6.'), 'rate', 6)).toBe('6.')
    expect(formatElevationAdjustmentInput(rateInput('6.'), 'adjustment', 1.2)).toBe('1.2')
    expect(formatElevationAdjustmentInput(rateInput('6.'), 'adjustment', null)).toBe('')
    expect(formatElevationAdjustmentInput(rateInput('6.'), 'adjustment', Infinity)).toBe('')
  })
})
