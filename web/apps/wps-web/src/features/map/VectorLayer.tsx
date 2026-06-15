import { MapContext } from 'features/map/Map'
import type Feature from 'ol/Feature'
import type Geometry from 'ol/geom/Geometry'
import OLVectorLayer from 'ol/layer/Vector'
import type VectorSource from 'ol/source/Vector'
import type { StyleLike } from 'ol/style/Style'
import React, { useContext, useEffect, useState } from 'react'

interface Props {
  source: VectorSource<Feature<Geometry>>
  style: StyleLike
  opacity?: number
  zIndex?: number
}

const VectorLayer = ({ source, style, opacity, zIndex = 0 }: Props) => {
  const map = useContext(MapContext)

  const [layer, setLayer] = useState<OLVectorLayer | null>(null)

  useEffect(() => {
    if (!map) return

    const vectorLayer = new OLVectorLayer({
      source,
      style,
      opacity,
      zIndex
    })

    map.addLayer(vectorLayer)
    vectorLayer.setZIndex(zIndex)
    setLayer(vectorLayer)

    return () => {
      if (map) {
        map.removeLayer(vectorLayer)
      }
    }
  }, [map])

  useEffect(() => {
    if (!layer) return

    layer.setSource(source)
  }, [source])

  useEffect(() => {
    if (!layer) return

    layer.setStyle(style)
  }, [style])

  return null
}

export default React.memo(VectorLayer)
