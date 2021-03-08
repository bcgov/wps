import React, { useContext, useEffect } from 'react'
import OLVectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { StyleLike } from 'ol/style/Style'

import { MapContext } from 'features/map/Map'

interface Props {
  source: VectorSource
  style: StyleLike
  opacity?: number
  zIndex?: number
}

const VectorLayer = ({ source, style, opacity, zIndex = 0 }: Props) => {
  const map = useContext(MapContext)!

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

    return () => {
      if (map) {
        map.removeLayer(vectorLayer)
      }
    }
  }, [map]) // eslint-disable-line react-hooks/exhaustive-deps

  return null
}

export default React.memo(VectorLayer)
