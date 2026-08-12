import { describe, expect, it } from 'vitest'
import { RunType } from './runType'

describe('RunType', () => {
  it('uses the lowercase API representation', () => {
    expect(RunType.ACTUAL).toBe('actual')
    expect(RunType.FORECAST).toBe('forecast')
  })
})
