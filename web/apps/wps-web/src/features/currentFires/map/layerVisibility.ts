export const CURRENT_FIRE_STATUS_OPTIONS = ['Out of Control', 'Being Held', 'Under Control'] as const
export type CurrentFireStatus = (typeof CURRENT_FIRE_STATUS_OPTIONS)[number]

export const DEFAULT_CURRENT_FIRE_STATUS_VISIBILITY: Record<CurrentFireStatus, boolean> = {
  'Out of Control': true,
  'Being Held': true,
  'Under Control': false
}

export const getVisibleCurrentFireStatusDefaults = (): CurrentFireStatus[] =>
  CURRENT_FIRE_STATUS_OPTIONS.filter(status => DEFAULT_CURRENT_FIRE_STATUS_VISIBILITY[status])
