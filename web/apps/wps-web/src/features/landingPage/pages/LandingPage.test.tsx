import { getFeedback } from '@sentry/react'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MS_TEAMS_SPRINT_REVIEW_URL } from '@wps/utils/env'
import { fbpGoInfo, percentileCalcInfo, toolInfos, weatherToolkitInfo } from 'features/landingPage/toolInfo'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { sfmsDailyFireWeatherIndexInfo, wxDataViewerInfo, wxNetworkAlertsInfo } from '../ExternalToolInfos'
import { LANDING_PAGE_FAVOURITES_STORAGE_KEY } from '../favouritesStorage'
import { apiTools, bcpsTools, publicTools } from '../landingPageTools'
import { BCWS_PREDICTIVE_SERVICES_MANAGED_BY } from '../managedBy'
import LandingPage from './LandingPage'

vi.mock('@sentry/react', () => ({
  getFeedback: vi.fn()
}))

vi.mock('@wps/utils/env', async importOriginal => {
  const actual = await importOriginal<typeof import('@wps/utils/env')>()
  return {
    ...actual,
    MS_TEAMS_SPRINT_REVIEW_URL: 'https://teams.microsoft.com/l/meetup-join/sprint-reviews'
  }
})

const LocationDisplay = () => {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

const renderPage = () =>
  render(
    <MemoryRouter>
      <LandingPage />
      <LocationDisplay />
    </MemoryRouter>
  )

const mockGetFeedback = vi.mocked(getFeedback)

describe('LandingPage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('shows the access and collaboration information in the header', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(screen.getByRole('heading', { name: 'Predictive Services Tools & Applications' })).toBeInTheDocument()
    expect(screen.getByText(/BCPS Access Only tools require a BC Government account/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'B.C. Wildfire Service' })).toHaveAttribute(
      'href',
      'https://www2.gov.bc.ca/gov/content/safety/wildfire-status'
    )
    const sprintReviewsLink = screen.getByRole('link', { name: /Sprint Reviews/ })
    expect(sprintReviewsLink).toHaveAttribute('href', MS_TEAMS_SPRINT_REVIEW_URL)
    await user.hover(sprintReviewsLink)
    expect(await screen.findByText('Wednesdays at 1:00 PM on non-pay weeks')).toBeInTheDocument()
    expect(screen.getByText('Collaboard', { selector: 'a' })).toBeInTheDocument()
  })

  it('shows tools in their configured sections', () => {
    renderPage()

    const accessSection = screen.getByRole('region', { name: 'BCPS Access Only' })
    for (const tool of bcpsTools) {
      expect(within(accessSection).getByRole('heading', { name: tool.name })).toBeInTheDocument()
    }
    expect(within(accessSection).queryByText(fbpGoInfo.name)).not.toBeInTheDocument()
    expect(within(accessSection).queryByText(percentileCalcInfo.name)).not.toBeInTheDocument()
    expect(within(accessSection).queryByText(weatherToolkitInfo.name)).not.toBeInTheDocument()
    expect(within(accessSection).queryByText(wxDataViewerInfo.name)).not.toBeInTheDocument()
    expect(within(accessSection).queryByText(wxNetworkAlertsInfo.name)).not.toBeInTheDocument()
    expect(within(accessSection).queryByText(sfmsDailyFireWeatherIndexInfo.name)).not.toBeInTheDocument()
    const publicSection = screen.getByRole('region', { name: 'Public Access' })
    for (const tool of publicTools) {
      expect(within(publicSection).getByText(tool.name)).toBeInTheDocument()
    }
    expect(within(publicSection).queryByText(sfmsDailyFireWeatherIndexInfo.name)).not.toBeInTheDocument()
    const apiSection = screen.getByRole('region', { name: 'API Access' })
    for (const tool of apiTools) {
      expect(within(apiSection).getByText(tool.name)).toBeInTheDocument()
    }
    const sfmsApiCard = within(apiSection)
      .getByRole('heading', { name: sfmsDailyFireWeatherIndexInfo.name })
      .closest('article')
    expect(
      screen.getByText('A dashboard to visualize and monitor sensor performance using hourly weather observations.')
    ).toBeInTheDocument()
    expect(within(sfmsApiCard as HTMLElement).getByRole('link', { name: 'here' })).toHaveAttribute(
      'href',
      'https://wfapps.nrs.gov.bc.ca/pub/wfwx-info-war/sfms'
    )
    expect(screen.getByRole('img', { name: 'Auto Spatial Advisory logo' })).toHaveAttribute(
      'src',
      '/images/asa-go-logo.png'
    )
    expect(screen.getAllByRole('link', { name: 'CSBC - Predictive Services' })).toHaveLength(
      toolInfos.length + apiTools.length
    )
    const bcwsManagedByLinks = screen.getAllByRole('link', { name: BCWS_PREDICTIVE_SERVICES_MANAGED_BY.name })
    expect(bcwsManagedByLinks).toHaveLength(2)
    for (const managedByLink of bcwsManagedByLinks) {
      expect(managedByLink).toHaveAttribute('href', BCWS_PREDICTIVE_SERVICES_MANAGED_BY.href)
    }
  })

  it('opens the feedback form from the CSBC managed by link', async () => {
    const user = userEvent.setup()
    const mockForm = {
      appendToDom: vi.fn(),
      open: vi.fn()
    }
    const mockCreateForm = vi.fn().mockResolvedValue(mockForm)
    mockGetFeedback.mockReturnValue({ createForm: mockCreateForm } as unknown as ReturnType<typeof getFeedback>)
    renderPage()

    await user.click(screen.getAllByRole('link', { name: 'CSBC - Predictive Services' })[0])

    await waitFor(() => {
      expect(mockCreateForm).toHaveBeenCalled()
      expect(mockForm.appendToDom).toHaveBeenCalled()
      expect(mockForm.open).toHaveBeenCalled()
    })
  })

  it('only opens explicitly external tools in a new tab', () => {
    renderPage()

    const publicSection = screen.getByRole('region', { name: 'Public Access' })
    const fbpGoCard = within(publicSection).getByRole('heading', { name: fbpGoInfo.name }).closest('article')
    const wxDataViewerCard = within(publicSection)
      .getByRole('heading', { name: wxDataViewerInfo.name })
      .closest('article')
    const wxNetworkAlertsCard = within(publicSection)
      .getByRole('heading', { name: wxNetworkAlertsInfo.name })
      .closest('article')
    const apiSection = screen.getByRole('region', { name: 'API Access' })
    const sfmsDailyFireWeatherIndexCard = within(apiSection)
      .getByRole('heading', { name: sfmsDailyFireWeatherIndexInfo.name })
      .closest('article')
    const fbpGoTitleLink = within(fbpGoCard as HTMLElement).getByRole('link', { name: fbpGoInfo.name })
    const wxDataViewerTitleLink = within(wxDataViewerCard as HTMLElement).getByRole('link', {
      name: wxDataViewerInfo.name
    })
    const wxNetworkAlertsTitleLink = within(wxNetworkAlertsCard as HTMLElement).getByRole('link', {
      name: wxNetworkAlertsInfo.name
    })
    const sfmsDailyFireWeatherIndexTitleLink = within(sfmsDailyFireWeatherIndexCard as HTMLElement).getByRole('link', {
      name: sfmsDailyFireWeatherIndexInfo.name
    })

    expect(within(fbpGoCard as HTMLElement).getByRole('link', { name: 'Open' })).toHaveAttribute('target', '_blank')
    expect(within(fbpGoCard as HTMLElement).getByRole('link', { name: 'Open' })).toHaveAttribute('rel', 'noreferrer')
    expect(fbpGoTitleLink).toHaveAttribute('href', fbpGoInfo.route)
    expect(fbpGoTitleLink).toHaveAttribute('target', '_blank')
    expect(fbpGoTitleLink).toHaveAttribute('rel', 'noreferrer')
    expect(within(wxDataViewerCard as HTMLElement).getByRole('link', { name: 'Open' })).toHaveAttribute(
      'target',
      '_blank'
    )
    expect(within(wxDataViewerCard as HTMLElement).getByRole('link', { name: 'Open' })).toHaveAttribute(
      'rel',
      'noreferrer'
    )
    expect(wxDataViewerTitleLink).toHaveAttribute('href', wxDataViewerInfo.route)
    expect(wxDataViewerTitleLink).toHaveAttribute('target', '_blank')
    expect(wxDataViewerTitleLink).toHaveAttribute('rel', 'noreferrer')
    expect(within(wxNetworkAlertsCard as HTMLElement).getByRole('link', { name: 'Open' })).toHaveAttribute(
      'target',
      '_blank'
    )
    expect(wxNetworkAlertsTitleLink).toHaveAttribute('href', wxNetworkAlertsInfo.route)
    expect(wxNetworkAlertsTitleLink).toHaveAttribute('target', '_blank')
    expect(wxNetworkAlertsTitleLink).toHaveAttribute('rel', 'noreferrer')
    expect(within(sfmsDailyFireWeatherIndexCard as HTMLElement).getByRole('link', { name: 'Open' })).toHaveAttribute(
      'target',
      '_blank'
    )
    expect(sfmsDailyFireWeatherIndexTitleLink).toHaveAttribute('href', sfmsDailyFireWeatherIndexInfo.route)
    expect(sfmsDailyFireWeatherIndexTitleLink).toHaveAttribute('target', '_blank')
    expect(sfmsDailyFireWeatherIndexTitleLink).toHaveAttribute('rel', 'noreferrer')
  })

  it('uses router navigation for internal tool links', async () => {
    const user = userEvent.setup()
    renderPage()

    const publicSection = screen.getByRole('region', { name: 'Public Access' })
    const percentileCalculatorCard = within(publicSection)
      .getByRole('heading', { name: percentileCalcInfo.name })
      .closest('article')

    await user.click(within(percentileCalculatorCard as HTMLElement).getByRole('link', { name: 'Open' }))

    expect(screen.getByTestId('location')).toHaveTextContent(percentileCalcInfo.route)
  })

  it('uses router navigation for internal quick access links', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Open quick access' }))
    const quickAccess = screen.getByRole('navigation', { name: 'Quick access' })

    await user.click(within(quickAccess).getByRole('link', { name: percentileCalcInfo.name }))

    expect(screen.getByTestId('location')).toHaveTextContent(percentileCalcInfo.route)
  })

  it('opens external quick access links in a new tab', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Open quick access' }))
    const quickAccess = screen.getByRole('navigation', { name: 'Quick access' })
    const fbpGoLink = within(quickAccess).getByRole('link', { name: /FBP Go/ })
    const wxDataViewerLink = within(quickAccess).getByRole('link', { name: wxDataViewerInfo.name })

    expect(fbpGoLink).toHaveAttribute('href', fbpGoInfo.route)
    expect(fbpGoLink).toHaveAttribute('target', '_blank')
    expect(fbpGoLink).toHaveAttribute('rel', 'noreferrer')
    expect(wxDataViewerLink).toHaveAttribute('href', wxDataViewerInfo.route)
    expect(wxDataViewerLink).toHaveAttribute('target', '_blank')
    expect(wxDataViewerLink).toHaveAttribute('rel', 'noreferrer')
  })

  it('moves a favourited tool out of its access section and persists it', async () => {
    const user = userEvent.setup()
    renderPage()

    const accessSection = screen.getByRole('region', { name: 'BCPS Access Only' })
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
      within(screen.getByRole('region', { name: 'BCPS Access Only' })).queryByText(tool.name)
    ).not.toBeInTheDocument()
  })

  it('shows support email links in the quick access menu', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Open quick access' }))

    expect(await screen.findByText('SUPPORT')).toBeInTheDocument()
    expect(screen.getByText(/please use the Submit Feedback in-app functionality/)).toBeInTheDocument()
    expect(screen.getByText('After-hours support:')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'BCWS.TechServices@gov.bc.ca' })).toHaveAttribute(
      'href',
      'mailto:BCWS.TechServices@gov.bc.ca'
    )
  })
})
