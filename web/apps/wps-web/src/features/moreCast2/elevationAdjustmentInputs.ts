export interface ElevationAdjustmentInput {
  field: 'rate' | 'adjustment'
  value: string
}

const roundInput = (value: number): number => Number(value.toFixed(1))

const parseInput = (value: string): number | null => {
  if (value.trim() === '') return null

  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return null

  return roundInput(parsed)
}

export const calculateElevationAdjustmentInputs = (input: ElevationAdjustmentInput, differenceKm: number | null) => {
  const canConvert = differenceKm !== null && differenceKm !== 0
  const entered = parseInput(input.value)
  let rate: number | null = null
  let adjustment: number | null = null

  if (entered === null) return { rate, adjustment, canConvert }

  if (input.field === 'rate') {
    rate = entered
    if (differenceKm !== null) adjustment = roundInput(rate * differenceKm)
  } else {
    adjustment = entered
    if (canConvert) rate = roundInput(adjustment / differenceKm!)
  }

  return { rate, adjustment, canConvert }
}

export const formatElevationAdjustmentInput = (
  input: ElevationAdjustmentInput,
  field: ElevationAdjustmentInput['field'],
  value: number | null
): string => {
  if (input.field === field) return input.value
  if (value === null || !Number.isFinite(value)) return ''
  return value.toFixed(1)
}
