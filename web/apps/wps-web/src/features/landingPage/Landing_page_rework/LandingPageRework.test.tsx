import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MS_TEAMS_SPRINT_REVIEW_URL } from '@wps/utils/env'
import { fbpGoInfo, toolInfos } from 'features/landingPage/toolInfo'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LandingPageRework, { LANDING_PAGE_FAVOURITES_STORAGE_KEY } from './LandingPageRework'

vi.mock('@wps/utils/env', async importOriginal => {
  const actual = await importOriginal<typeof import('@wps/utils/env')>()
  return {
    ...actual,
    MS_TEAMS_SPRINT_REVIEW_URL: 'https://teams.microsoft.com/l/meetup-join/sprint-reviews'
  }
})

const renderPage = () =>
  render(
    <MemoryRouter>
      <LandingPageRework />
    </MemoryRouter>
  )

describe('LandingPageRework', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('shows the access and collaboration information in the header', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(screen.getByRole('heading', { name: 'Predictive Services Tools & Applications' })).toBeInTheDocument()
    expect(screen.getByText(/BCPS Access Only tools require a BC Government account/)).toBeInTheDocument()
    const sprintReviewsLink = screen.getByRole('link', { name: /Sprint Reviews/ })
    expect(sprintReviewsLink).toHaveAttribute('href', MS_TEAMS_SPRINT_REVIEW_URL)
    await user.hover(sprintReviewsLink)
    expect(await screen.findByText('Wednesdays at 1:00 PM on non-pay weeks')).toBeInTheDocument()
    expect(screen.getByText('Collaboard', { selector: 'a' })).toBeInTheDocument()
  })

  it('shows FBP Go publicly and the remaining tools in the BCWS access section', () => {
    renderPage()

    const accessSection = screen.getByRole('region', { name: 'BCWS Access Only' })
    for (const tool of toolInfos.filter(toolInfo => toolInfo.route !== fbpGoInfo.route)) {
      expect(within(accessSection).getByRole('heading', { name: tool.name })).toBeInTheDocument()
    }
    expect(within(accessSection).queryByText(fbpGoInfo.name)).not.toBeInTheDocument()
    expect(within(screen.getByRole('region', { name: 'Public Access' })).getByText(fbpGoInfo.name)).toBeInTheDocument()
    expect(screen.getAllByText('Managed by: (Team Name)')).toHaveLength(toolInfos.length)
  })

  it('moves a favourited tool out of its access section and persists it', async () => {
    const user = userEvent.setup()
    renderPage()

    const accessSection = screen.getByRole('region', { name: 'BCWS Access Only' })
    const tool = toolInfos[0]
    await user.click(within(accessSection).getByRole('button', { name: `Add ${tool.name} to favourites` }))

    expect(within(screen.getByRole('region', { name: 'My Favourites' })).getByText(tool.name)).toBeInTheDocument()
    expect(within(accessSection).queryByText(tool.name)).not.toBeInTheDocument()
    await waitFor(() => {
      expect(JSON.parse(localStorage.getItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY) ?? '[]')).toEqual([tool.route])
    })
  })

  it('restores favourites from local storage', () => {
    const tool = toolInfos[0]
    localStorage.setItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY, JSON.stringify([tool.route]))

    renderPage()

    expect(within(screen.getByRole('region', { name: 'My Favourites' })).getByText(tool.name)).toBeInTheDocument()
    expect(
      within(screen.getByRole('region', { name: 'BCWS Access Only' })).queryByText(tool.name)
    ).not.toBeInTheDocument()
  })

  it('shows support email links in the quick access menu', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Open quick access' }))

    expect(await screen.findByText('SUPPORT')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'BCWS.PredictiveServices@gov.bc.ca' })).toHaveAttribute(
      'href',
      'mailto:BCWS.PredictiveServices@gov.bc.ca'
    )
    expect(screen.getByRole('link', { name: 'BCWS.TechServices@gov.bc.ca' })).toHaveAttribute(
      'href',
      'mailto:BCWS.TechServices@gov.bc.ca'
    )
  })
})
