import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import SpotMapLayerSwitcher from './SpotMapLayerSwitcher'
import { getVisibleCurrentFireStatusDefaults } from './mapLayerVisibility'

const STATUS_OPTIONS = [SpotRequestStatus.REQUESTED, SpotRequestStatus.STARTED]

const baseProps = {
  statusOptions: STATUS_OPTIONS,
  selectedStatuses: STATUS_OPTIONS,
  currentFiresVisible: true,
  selectedCurrentFireStatuses: getVisibleCurrentFireStatusDefaults(),
  onStatusChange: vi.fn(),
  onAllStatusesChange: vi.fn(),
  onCurrentFiresVisibleChange: vi.fn(),
  onCurrentFireStatusChange: vi.fn()
}

describe('SpotMapLayerSwitcher — fire number filter', () => {
  it('renders the fire number section when fire number props are provided', () => {
    render(
      <SpotMapLayerSwitcher
        {...baseProps}
        allFireNumbers={['V1234567', 'V9999999']}
        selectedFireNumbers={[]}
        onFireNumbersChange={vi.fn()}
      />
    )
    expect(screen.getByText('Fire Number')).toBeInTheDocument()
  })

  it('does not render the fire number section when fire number props are omitted', () => {
    render(<SpotMapLayerSwitcher {...baseProps} />)
    expect(screen.queryByText('Fire Number')).not.toBeInTheDocument()
  })

  it('shows "All fires" placeholder when no fire numbers are selected', () => {
    render(
      <SpotMapLayerSwitcher
        {...baseProps}
        allFireNumbers={['V1234567']}
        selectedFireNumbers={[]}
        onFireNumbersChange={vi.fn()}
      />
    )
    expect(screen.getByPlaceholderText('All fires')).toBeInTheDocument()
  })

  it('hides the placeholder when fire numbers are selected', () => {
    render(
      <SpotMapLayerSwitcher
        {...baseProps}
        allFireNumbers={['V1234567']}
        selectedFireNumbers={['V1234567']}
        onFireNumbersChange={vi.fn()}
      />
    )
    expect(screen.queryByPlaceholderText('All fires')).not.toBeInTheDocument()
  })

  it('calls onFireNumbersChange when an option is selected', async () => {
    const onFireNumbersChange = vi.fn()
    render(
      <SpotMapLayerSwitcher
        {...baseProps}
        allFireNumbers={['V1234567', 'V9999999']}
        selectedFireNumbers={[]}
        onFireNumbersChange={onFireNumbersChange}
      />
    )

    await userEvent.click(screen.getByPlaceholderText('All fires'))
    await userEvent.click(screen.getByText('V1234567'))

    expect(onFireNumbersChange).toHaveBeenCalledWith(['V1234567'])
  })

  it('calls onFireNumbersChange with multiple selections', async () => {
    const onFireNumbersChange = vi.fn()
    render(
      <SpotMapLayerSwitcher
        {...baseProps}
        allFireNumbers={['V1234567', 'V9999999']}
        selectedFireNumbers={['V1234567']}
        onFireNumbersChange={onFireNumbersChange}
      />
    )

    // open dropdown and pick second option
    await userEvent.click(screen.getByRole('combobox'))
    await userEvent.click(screen.getByText('V9999999'))

    expect(onFireNumbersChange).toHaveBeenCalledWith(['V1234567', 'V9999999'])
  })
})
