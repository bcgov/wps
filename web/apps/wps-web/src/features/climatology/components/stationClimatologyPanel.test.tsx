import { render, screen } from '@testing-library/react'
import type { ClimatologyViewProps } from '@/features/climatology/components/ClimatologyView'
import StationClimatologyPanel from './StationClimatologyPanel'

vi.mock('@/features/climatology/components/ClimatologyView', () => ({
  default: ({ stations, groupLabel, emptyMessage }: ClimatologyViewProps) => (
    <div
      data-testid="climatology-view"
      data-stations={stations.map(station => `${station.code}:${station.name}`).join(',')}
      data-label={groupLabel ?? ''}
    >
      {stations.length === 0 && emptyMessage}
    </div>
  )
}))

describe('StationClimatologyPanel', () => {
  it('says how to choose stations on the map', () => {
    render(<StationClimatologyPanel chosen={[]} label={null} error={null} />)

    expect(screen.getByText(/Click a station on the map, or draw an area/)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('charts the stations chosen, under the name of a drawn area', () => {
    render(
      <StationClimatologyPanel
        chosen={[
          { code: 322, name: 'AFTON' },
          { code: 209, name: 'ALEXIS CREEK' }
        ]}
        label="2 stations in the drawn area"
        error={null}
      />
    )

    expect(screen.getByTestId('climatology-view')).toHaveAttribute('data-stations', '322:AFTON,209:ALEXIS CREEK')
    expect(screen.getByTestId('climatology-view')).toHaveAttribute('data-label', '2 stations in the drawn area')
  })

  it('says when the stations could not be loaded', () => {
    render(<StationClimatologyPanel chosen={[]} label={null} error="Network Error" />)

    expect(screen.getByRole('alert')).toHaveTextContent('could not be loaded')
  })
})
