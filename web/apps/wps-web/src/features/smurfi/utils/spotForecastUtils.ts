import { DateTime } from 'luxon'
import { RepresentativeStation } from '@/features/smurfi/interfaces'

export const TIMEZONE = 'America/Vancouver'

export const formatDateTime = (iso: string): string => {
  const dt = DateTime.fromISO(iso).setZone(TIMEZONE)
  return dt.isValid ? `${dt.toFormat('HH:mm')} ${dt.offsetNameShort} ${dt.toFormat('EEE, MMM d, yyyy')}` : iso
}

export const formatStationsStr = (stations: RepresentativeStation[]): string =>
  stations.length > 0
    ? stations.map(s => s.name + (s.elevation == null ? '' : ` (${s.elevation}m)`)).join(', ')
    : '—'
