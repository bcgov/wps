import type { DateTime } from 'luxon'
import { ASA_GO_TIMEZONE } from '@/utils/constants'

export const getHFIRunDateKey = (runDate: DateTime) => runDate.setZone(ASA_GO_TIMEZONE).toISODate()!
