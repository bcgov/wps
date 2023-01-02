import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReadyPlanningAreaDetails } from 'api/hfiCalculatorAPI'
import PlanningAreaReadyToggle from 'features/hfiCalculator/components/PlanningAreaReadyToggle'
import { DateTime } from 'luxon'
import { vi } from 'vitest'
import React from 'react'

describe('PlanningAreaReadyToggle', () => {
  const readyDetails: ReadyPlanningAreaDetails = {
    planning_area_id: 1,
    hfi_request_id: 1,
    ready: true,
    create_timestamp: DateTime.fromObject({ year: 2021, month: 1, day: 1 }),
    create_user: 'test',
    update_timestamp: DateTime.fromObject({ year: 2021, month: 1, day: 1 }),
    update_user: 'test'
  }
  const toggleMockFn = vi.fn((): void => {
    /** no op */
  })
  beforeEach(() => {
    toggleMockFn.mockReset()
  })
  it('should render tooltip text when ready is true and enabled', () => {
    const { getByTestId, getByLabelText } = render(
      <PlanningAreaReadyToggle enabled={true} loading={false} toggleReady={toggleMockFn} readyDetails={readyDetails} />
    )
    const tooltip = getByTestId('hfi-ready-tooltip')
    const tooltipText = getByLabelText(
      `Marked ready by ${readyDetails?.update_user} at ${readyDetails?.update_timestamp.toISO()}`
    )
    expect(tooltip).toBeDefined()
    expect(tooltipText).toBeDefined()
  })
  it('should render tooltip text when ready is true and not enabled', () => {
    const { getByTestId, getByLabelText } = render(
      <PlanningAreaReadyToggle enabled={false} loading={false} toggleReady={toggleMockFn} readyDetails={readyDetails} />
    )
    const tooltip = getByTestId('hfi-ready-tooltip')
    const tooltipText = getByLabelText(
      `Marked ready by ${readyDetails?.update_user} at ${readyDetails?.update_timestamp.toISO()}`
    )
    expect(tooltip).toBeDefined()
    expect(tooltipText).toBeDefined()
  })
  it('should call toggle callback when toggle button is clicked', async () => {
    const { getByTestId } = render(
      <PlanningAreaReadyToggle enabled={true} loading={false} toggleReady={toggleMockFn} readyDetails={readyDetails} />
    )
    const togglebutton = getByTestId('hfi-toggle-ready')

    togglebutton.focus()
    userEvent.click(togglebutton)

    await waitFor(() => expect(toggleMockFn).toHaveBeenCalledTimes(1))
  })
  it('should render the button disabled if no ready state exists', () => {
    const { getByTestId } = render(
      <PlanningAreaReadyToggle enabled={true} loading={false} toggleReady={toggleMockFn} />
    )
    const toggleButton = getByTestId('hfi-toggle-ready')
    expect(toggleButton).toBeDisabled()
  })
  it('should render the button disabled if not enabled', () => {
    const { getByTestId } = render(
      <PlanningAreaReadyToggle enabled={false} loading={false} toggleReady={toggleMockFn} />
    )
    const toggleButton = getByTestId('hfi-toggle-ready')
    expect(toggleButton).toBeDisabled()
  })
  it('should render the button with ToggleOnOutlineIcon when area is ready', () => {
    const { getByTestId } = render(
      <PlanningAreaReadyToggle enabled={true} loading={false} toggleReady={toggleMockFn} readyDetails={readyDetails} />
    )
    const onIcon = getByTestId('ToggleOnOutlinedIcon')
    expect(onIcon).toBeDefined()
  })
  it('should render the button with ToggleOffOutlinedIcon when area is not ready', () => {
    const notReadyDetails = { ...readyDetails, ready: false }
    const { getByTestId } = render(
      <PlanningAreaReadyToggle
        enabled={true}
        loading={false}
        toggleReady={toggleMockFn}
        readyDetails={notReadyDetails}
      />
    )
    const offIcon = getByTestId('ToggleOffOutlinedIcon')
    expect(offIcon).toBeDefined()
  })
  it('should render the button with ToggleOffOutlinedIcon when area has no ready details', () => {
    const { getByTestId } = render(
      <PlanningAreaReadyToggle enabled={true} loading={false} toggleReady={toggleMockFn} />
    )
    const offIcon = getByTestId('ToggleOffOutlinedIcon')
    expect(offIcon).toBeDefined()
  })
})
