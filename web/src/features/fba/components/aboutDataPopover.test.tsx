import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import AboutDataPopover from 'features/fba/components/AboutDataPopover'

const ADVISORY_THRESHOLD = 20

describe('AboutDataPopover', () => {
  it('should render the About Data Popover', () => {
    const { getByTestId } = render(<AboutDataPopover advisoryThreshold={ADVISORY_THRESHOLD}></AboutDataPopover>)
    const aboutData = getByTestId('about-data-popover')
    expect(aboutData).toBeInTheDocument()
  })
  it('should open the popover when clicked', () => {
    render(<AboutDataPopover advisoryThreshold={ADVISORY_THRESHOLD}></AboutDataPopover>)

    fireEvent.click(screen.getByTestId('about-data-trigger'))

    expect(screen.getByTestId('about-data-content')).toBeVisible()
    expect(screen.getByTestId('about-data-content')).toHaveTextContent(`${ADVISORY_THRESHOLD}%`)
  })
  it('should close the popover when clicking outside of it', async () => {
    render(<AboutDataPopover advisoryThreshold={ADVISORY_THRESHOLD}></AboutDataPopover>)
    fireEvent.click(screen.getByTestId('about-data-trigger'))
    expect(screen.getByTestId('about-data-content')).toBeVisible()

    fireEvent.click(document.body)
    await waitFor(() => {
      expect(screen.queryByTestId('popover-title')).not.toBeInTheDocument()
    })
  })
  it('should contain the advisory threshold as a percent', () => {
    render(<AboutDataPopover advisoryThreshold={ADVISORY_THRESHOLD}></AboutDataPopover>)

    fireEvent.click(screen.getByTestId('about-data-trigger'))

    expect(screen.getByTestId('about-data-content')).toBeVisible()
    expect(screen.getByTestId('about-data-content')).toHaveTextContent(`${ADVISORY_THRESHOLD}%`)
  })
})
