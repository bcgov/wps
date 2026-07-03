import { useMediaQuery } from '@mui/material'
import { ThemeProvider } from '@mui/material/styles'
import { renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useIsXSSmallScreen } from '@/hooks/useIsXSScreen'
import { theme } from '@/theme'

vi.mock('@mui/material', async () => {
  const actual = await vi.importActual<typeof import('@mui/material')>('@mui/material')

  return {
    ...actual,
    useMediaQuery: vi.fn()
  }
})

describe('useIsXSSmallScreen', () => {
  const wrapper = ({ children }: { children: ReactNode }) => <ThemeProvider theme={theme}>{children}</ThemeProvider>

  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns true when the media query matches', () => {
    vi.mocked(useMediaQuery).mockReturnValue(true)

    const { result } = renderHook(() => useIsXSSmallScreen(), { wrapper })

    expect(result.current).toBe(true)
  })

  it('returns false when the media query does not match', () => {
    vi.mocked(useMediaQuery).mockReturnValue(false)

    const { result } = renderHook(() => useIsXSSmallScreen(), { wrapper })

    expect(result.current).toBe(false)
  })

  it('uses a query that matches when either dimension is below the sm threshold', () => {
    vi.mocked(useMediaQuery).mockReturnValue(false)

    renderHook(() => useIsXSSmallScreen(), { wrapper })

    expect(useMediaQuery).toHaveBeenCalledWith(
      `(max-width:${theme.breakpoints.values.sm}px) or (max-height:${theme.breakpoints.values.sm}px)`
    )
  })
})
