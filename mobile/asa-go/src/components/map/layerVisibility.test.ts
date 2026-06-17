import VectorTileLayer from 'ol/layer/VectorTile'
import { vi } from 'vitest'
import type { FireShapeStatusDetail } from '@/api/fbaAPI'
import * as featureStylers from '@/featureStylers'
import { setZoneStatusLayerVisibility } from './layerVisibility'

describe('setZoneStatusLayerVisibility', () => {
  it('calls setStyle with a function from fireShapeStyler and that function returns a Style', () => {
    const layer = new VectorTileLayer()
    const fireShapeStatusDetail: FireShapeStatusDetail[] = []
    const visible = true

    const setStyleSpy = vi.spyOn(layer, 'setStyle')
    const fireShapeStylerSpy = vi.spyOn(featureStylers, 'fireShapeStyler')

    setZoneStatusLayerVisibility(layer, fireShapeStatusDetail, visible)

    expect(setStyleSpy).toHaveBeenCalled()
    expect(fireShapeStylerSpy).toHaveBeenCalledWith(expect.any(Array), visible)

    const styleFn = setStyleSpy.mock.calls[0][0]
    expect(typeof styleFn).toBe('function')
  })
})
