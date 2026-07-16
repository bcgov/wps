import { render, screen } from '@testing-library/react'
import { DateTime } from 'luxon'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { StatusEnum } from '@/utils/constants'
import InfoBar from './InfoBar'

const viewingDate = DateTime.fromISO('2024-07-15')

describe('InfoBar', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders viewing date in correct format', () => {
    render(<InfoBar viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" />)
    expect(screen.getByText(/Mon, Jul 15\./)).toBeInTheDocument()
  })

  it('renders valid until as today when the expiry is today', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T12:00:00'))
    const validUntil = DateTime.fromISO('2024-07-15T18:00:00').toUTC().toISO()

    render(<InfoBar validUntil={validUntil} viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" />)
    expect(screen.getByText(/Valid until: 18:00 Today\./)).toBeInTheDocument()
  })

  it('renders valid until as tomorrow when the expiry is tomorrow', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T12:00:00'))
    const validUntil = DateTime.fromISO('2024-07-16T08:00:00').toUTC().toISO()

    render(<InfoBar validUntil={validUntil} viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" />)
    expect(screen.getByText(/Valid until: 08:00 Tomorrow\./)).toBeInTheDocument()
  })

  it('renders valid until as a date when the expiry date is in the past', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-07-15T12:00:00'))
    const validUntil = DateTime.fromISO('2024-07-14T18:00:00').toUTC().toISO()

    render(<InfoBar validUntil={validUntil} viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" />)
    expect(screen.getByText(/Valid until: Jul 14, 18:00\./)).toBeInTheDocument()
  })

  it('renders n/a when validUntil is null', () => {
    render(<InfoBar validUntil={null} viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" />)
    expect(screen.getByText(/Valid until: n\/a\./)).toBeInTheDocument()
  })

  it('renders statusText when provided', () => {
    render(
      <InfoBar
        validUntil={null}
        viewingDate={viewingDate}
        status={StatusEnum.WARNING}
        Icon="icon.svg"
        statusText="Offline mode"
      />
    )
    expect(screen.getByText(/Offline mode/)).toBeInTheDocument()
  })

  it('renders when statusText is omitted', () => {
    render(<InfoBar validUntil={null} viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" />)
    expect(screen.queryByText(/Viewing/)).toBeInTheDocument()
  })

  it('renders when statusText is empty string', () => {
    render(
      <InfoBar validUntil={null} viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" statusText="" />
    )
    expect(screen.queryByText(/Viewing/)).toBeInTheDocument()
  })

  it('renders an img with the correct src', () => {
    render(<InfoBar validUntil={null} viewingDate={viewingDate} status={StatusEnum.INFO} Icon="network-icon.svg" />)
    const img = screen.getByRole('img')
    expect(img).toHaveAttribute('src', 'network-icon.svg')
  })

  it('renders Viewing: label', () => {
    render(<InfoBar validUntil={null} viewingDate={viewingDate} status={StatusEnum.INFO} Icon="icon.svg" />)
    expect(screen.queryByText(/Viewing:/)).toBeInTheDocument()
  })
})
