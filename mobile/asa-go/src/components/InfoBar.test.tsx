import { ThemeProvider } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { DateTime, Settings } from 'luxon'
import type { ComponentProps } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { theme } from '@/theme'
import { StatusEnum } from '@/utils/constants'
import InfoBar from './InfoBar'

const viewingDate = DateTime.fromISO('2024-07-15')
const renderInfoBar = (props: Partial<ComponentProps<typeof InfoBar>> = {}) =>
  render(
    <ThemeProvider theme={theme}>
      <InfoBar viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" {...props} />
    </ThemeProvider>
  )

describe('InfoBar', () => {
  beforeEach(() => {
    Settings.defaultZone = 'UTC-7'
  })
  afterEach(() => {
    vi.useRealTimers()
    Settings.defaultZone = 'system'
  })

  it('renders viewing date in correct format', () => {
    renderInfoBar()
    expect(screen.getByText(/Mon, Jul 15\./)).toBeInTheDocument()
  })

  it('renders valid until as today when the expiry is today', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T12:00:00'))
    const validUntil = DateTime.fromISO('2024-07-15T18:00:00').toUTC().toISO()

    renderInfoBar({ validUntil })
    expect(screen.getByText(/Valid until: 18:00 PDT Today\./)).toBeInTheDocument()
  })

  it('renders valid until as tomorrow when the expiry is tomorrow', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T12:00:00'))
    const validUntil = DateTime.fromISO('2024-07-16T08:00:00').toUTC().toISO()

    renderInfoBar({ validUntil })
    expect(screen.getByText(/Valid until: 08:00 PDT Tomorrow\./)).toBeInTheDocument()
  })

  it('renders valid until as midnight tonight when the expiry is local midnight tomorrow', () => {
    Settings.defaultZone = 'America/Vancouver'
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T19:00:00Z'))
    const validUntil = DateTime.fromISO('2024-07-16T00:00:00', {
      zone: 'America/Vancouver'
    })
      .toUTC()
      .toISO()

    renderInfoBar({ validUntil })
    expect(screen.getByText(/Valid until: Midnight Tonight PDT\./)).toBeInTheDocument()
  })

  it('uses BC midnight even when the device is in Toronto', () => {
    Settings.defaultZone = 'America/Toronto'
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T16:00:00Z'))
    const validUntil = DateTime.fromISO('2024-07-16T00:00:00', {
      zone: 'America/Vancouver'
    })
      .toUTC()
      .toISO()

    renderInfoBar({ validUntil })
    expect(screen.getByText(/Valid until: Midnight Tonight PDT\./)).toBeInTheDocument()
  })

  it.each(['America/Toronto', 'UTC', 'Asia/Tokyo'])('uses BC today near midnight on a %s device', zone => {
    Settings.defaultZone = zone
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-11-22T05:00:00Z'))
    renderInfoBar({ validUntil: '2026-11-22T06:00:00Z' })
    expect(screen.getByText(/Valid until: 23:00 PCT Today\./)).toBeInTheDocument()
  })

  it('labels the next BC day as tomorrow on a Tokyo device', () => {
    Settings.defaultZone = 'Asia/Tokyo'
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-11-22T05:00:00Z'))
    renderInfoBar({ validUntil: '2026-11-22T20:00:00Z' })
    expect(screen.getByText(/Valid until: 13:00 PCT Tomorrow\./)).toBeInTheDocument()
  })

  it('renders n/a for an invalid timestamp', () => {
    renderInfoBar({ validUntil: 'invalid' })
    expect(screen.getByText(/Valid until: n\/a\./)).toBeInTheDocument()
  })

  it('renders valid until as a date when the expiry date is in the past', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T12:00:00'))
    const validUntil = DateTime.fromISO('2024-07-14T18:00:00').toUTC().toISO()

    renderInfoBar({ validUntil })
    expect(screen.getByText(/Valid until: Jul 14, 18:00 PDT\./)).toBeInTheDocument()
  })

  it('renders n/a when validUntil is null', () => {
    renderInfoBar({ validUntil: null })
    expect(screen.getByText(/Valid until: n\/a\./)).toBeInTheDocument()
  })

  it('uses error colors when validUntil is in the past', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T12:00:00'))
    const validUntil = DateTime.fromISO('2024-07-14T18:00:00').toUTC().toISO()

    renderInfoBar({ validUntil })

    const infoBar = screen.getByText(/Valid until:/).parentElement
    expect(infoBar).toHaveStyle({
      backgroundColor: theme.palette.error.main,
      color: theme.palette.error.contrastText
    })
  })

  it('renders statusText when provided', () => {
    renderInfoBar({ validUntil: null, status: StatusEnum.WARNING, statusText: 'Offline mode' })
    expect(screen.getByText(/Offline mode/)).toBeInTheDocument()
  })

  it('renders when statusText is omitted', () => {
    renderInfoBar({ validUntil: null })
    expect(screen.queryByText(/Viewing/)).toBeInTheDocument()
  })

  it('renders when statusText is empty string', () => {
    renderInfoBar({ validUntil: null, statusText: '' })
    expect(screen.queryByText(/Viewing/)).toBeInTheDocument()
  })

  it('renders an img with the correct src', () => {
    renderInfoBar({ validUntil: null, Icon: 'network-icon.svg' })
    const img = screen.getByRole('img')
    expect(img).toHaveAttribute('src', 'network-icon.svg')
  })

  it('renders Viewing: label', () => {
    renderInfoBar({ validUntil: null })
    expect(screen.queryByText(/Viewing:/)).toBeInTheDocument()
  })
})
