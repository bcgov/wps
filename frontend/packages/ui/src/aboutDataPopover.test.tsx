import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import AboutDataPopover from './AboutDataPopover'

const ADVISORY_THRESHOLD = 4000
const staticContent = () => <div>test content</div>
const thresholdContent = () => <div>{ADVISORY_THRESHOLD}%</div>

describe('AboutDataPopover', () => {
  it('should render the About Data Popover with static content', () => {
    const { getByTestId } = render(<AboutDataPopover content={staticContent}></AboutDataPopover>)
    const aboutData = getByTestId('about-data-popover')
    expect(aboutData).toBeInTheDocument()
  })
  it('should open the popover when clicked', () => {
    render(<AboutDataPopover content={staticContent}></AboutDataPopover>)

    fireEvent.click(screen.getByTestId('about-data-trigger'))

    expect(screen.getByTestId('about-data-content')).toBeVisible()
  })
  it('should close the popover when clicking outside of it', async () => {
    render(<AboutDataPopover content={staticContent}></AboutDataPopover>)
    fireEvent.click(screen.getByTestId('about-data-trigger'))
    expect(screen.getByTestId('about-data-content')).toBeVisible()

    fireEvent.click(document.body)
    await waitFor(() => {
      expect(screen.queryByTestId('popover-title')).not.toBeInTheDocument()
    })
  })
  it('should contain the advisory threshold as a percent if passed as a prop', () => {
    render(<AboutDataPopover content={thresholdContent}></AboutDataPopover>)

    fireEvent.click(screen.getByTestId('about-data-trigger'))

    expect(screen.getByTestId('about-data-content')).toBeVisible()
    expect(screen.getByTestId('about-data-content')).toHaveTextContent(`${ADVISORY_THRESHOLD}%`)
  })
})
