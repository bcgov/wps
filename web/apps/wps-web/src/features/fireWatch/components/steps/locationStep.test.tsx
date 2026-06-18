import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { Dispatch, SetStateAction } from 'react'
import { beforeEach, describe, expect, it, vi, type Mock } from 'vitest'
import LocationStep from '@/features/fireWatch/components/steps/LocationStep'
import type { FireWatch } from '@/features/fireWatch/interfaces'
import { getBlankFireWatch } from '@/features/fireWatch/utils'

vi.mock('ol', () => ({
  Collection: class {},
  Map: class {
    setTarget = vi.fn()
    on = vi.fn()
    getInteractions = vi.fn(() => ({ clear: vi.fn() }))
    addInteraction = vi.fn()
  },
  View: class {}
}))

vi.mock('ol/Feature.js', () => ({
  default: class {
    getGeometry = vi.fn(() => null)
  }
}))

vi.mock('ol/geom', () => ({
  Point: class {
    coords: number[]
    constructor(coords: number[]) {
      this.coords = coords
    }
    getCoordinates = vi.fn(function (this: { coords: number[] }) {
      return this.coords
    })
  }
}))

vi.mock('ol/interaction/defaults', () => ({
  defaults: vi.fn(() => ({ forEach: vi.fn() }))
}))

vi.mock('ol/interaction/Translate.js', () => ({
  default: class {
    on = vi.fn()
  }
}))

vi.mock('ol/layer/Tile', () => ({ default: class {} }))
vi.mock('ol/layer/Vector.js', () => ({ default: class {} }))

vi.mock('ol/proj', () => ({
  fromLonLat: vi.fn(([lon, lat]: number[]) => [lon * 1000, lat * 1000]),
  toLonLat: vi.fn(([x, y]: number[]) => [x / 1000, y / 1000])
}))

vi.mock('ol/source/Vector.js', () => ({
  default: class {
    clear = vi.fn()
    addFeatures = vi.fn()
  }
}))

vi.mock('ol/style', () => ({
  Icon: class {},
  Style: class {}
}))

vi.mock('features/fireWeather/components/maps/constants', () => ({
  source: {}
}))

describe('LocationStep', () => {
  let mockSetFireWatch: Mock<Dispatch<SetStateAction<FireWatch>>>

  beforeEach(() => {
    mockSetFireWatch = vi.fn<Dispatch<SetStateAction<FireWatch>>>()
  })

  it('renders lat and lon text fields', () => {
    render(<LocationStep fireWatch={getBlankFireWatch()} setFireWatch={mockSetFireWatch} />)

    expect(screen.getByTestId('lat-input')).toBeInTheDocument()
    expect(screen.getByTestId('lon-input')).toBeInTheDocument()
  })

  it('formats and commits lat/lon when valid values are entered and the field is blurred', async () => {
    render(<LocationStep fireWatch={getBlankFireWatch()} setFireWatch={mockSetFireWatch} />)

    const latInput = screen.getByTestId('lat-input')
    const lonInput = screen.getByTestId('lon-input')

    fireEvent.change(latInput, { target: { value: '50' } })
    fireEvent.change(lonInput, { target: { value: '-120' } })
    fireEvent.blur(lonInput)

    await waitFor(() => {
      expect(latInput).toHaveValue('50.000000')
      expect(lonInput).toHaveValue('-120.000000')
      expect(mockSetFireWatch).toHaveBeenCalledOnce()
    })
  })

  it('clears geometry when lat or lon is empty on blur', async () => {
    let currentFireWatch = getBlankFireWatch()
    const setFireWatch = vi.fn<Dispatch<SetStateAction<FireWatch>>>().mockImplementation(updater => {
      currentFireWatch = typeof updater === 'function' ? updater(currentFireWatch) : updater
    })

    render(<LocationStep fireWatch={currentFireWatch} setFireWatch={setFireWatch} />)

    fireEvent.blur(screen.getByTestId('lon-input'))

    await waitFor(() => {
      expect(setFireWatch).toHaveBeenCalledOnce()
    })
    expect(currentFireWatch.geometry).toBeUndefined()
  })
})
