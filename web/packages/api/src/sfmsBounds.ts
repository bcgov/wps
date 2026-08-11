import type { RunType } from './runType'

export interface SFMSBoundsMinMax {
  minimum: string
  maximum: string
}

export type SFMSBoundsByRunType = Partial<Record<RunType, SFMSBoundsMinMax>>

export interface SFMSBounds {
  [year: string]: SFMSBoundsByRunType
}

export interface SFMSBoundsResponse {
  sfms_bounds: SFMSBounds
}
