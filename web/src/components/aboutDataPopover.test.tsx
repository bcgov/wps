import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import AboutDataPopover from '@/components/AboutDataPopover'
import { FBAAboutDataContent } from '@/features/fbaCalculator/components/FbaAboutDataContent'
import { ADVISORY_THRESHOLD, ASAAboutDataContent } from '@/features/fba/components/ASAAboutDataContent'

describe('AboutDataPopover', () => {
  it('should render the About Data Popover with static content', () => {
    const { getByTestId } = render(<AboutDataPopover content={FBAAboutDataContent}></AboutDataPopover>)
    const aboutData = getByTestId('about-data-popover')
    expect(aboutData).toBeInTheDocument()
  })
  it('should open the popover when clicked', () => {
    render(<AboutDataPopover content={FBAAboutDataContent}></AboutDataPopover>)

    fireEvent.click(screen.getByTestId('about-data-trigger'))

    expect(screen.getByTestId('about-data-content')).toBeVisible()
  })
  it('should close the popover when clicking outside of it', async () => {
    render(<AboutDataPopover content={FBAAboutDataContent}></AboutDataPopover>)
    fireEvent.click(screen.getByTestId('about-data-trigger'))
    expect(screen.getByTestId('about-data-content')).toBeVisible()

    fireEvent.click(document.body)
    await waitFor(() => {
      expect(screen.queryByTestId('popover-title')).not.toBeInTheDocument()
    })
  })
  it('should contain the advisory threshold as a percent if passed as a prop', () => {
    render(<AboutDataPopover content={ASAAboutDataContent}></AboutDataPopover>)

    fireEvent.click(screen.getByTestId('about-data-trigger'))

    expect(screen.getByTestId('about-data-content')).toBeVisible()
    expect(screen.getByTestId('about-data-content')).toHaveTextContent(`${ADVISORY_THRESHOLD}%`)
  })
})
