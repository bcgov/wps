import React, { useState, useContext, useEffect } from 'react'
import ImageSource from 'ol/source/Image'
import OLImageLayer from 'ol/layer/Image'

import { MapContext } from 'features/map/Map'

interface Props {
  source: ImageSource
  opacity?: number
  zIndex?: number
}

const ImageLayer = ({ source, opacity = 1, zIndex = 0 }: Props) => {
  const map = useContext(MapContext)

  const [layer, setLayer] = useState<OLImageLayer | null>(null)

  useEffect(() => {
    if (!map) return

    console.log('creating OLImageLayer')

    const imageLayer = new OLImageLayer({
      source,
      zIndex,
      opacity
    })

    map.addLayer(imageLayer)
    imageLayer.setZIndex(zIndex)
    setLayer(imageLayer)

    return () => {
      if (map) {
        map.removeLayer(imageLayer)
      }
    }
  }, [map]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!layer) return

    layer.setSource(source)
  }, [source]) // eslint-disable-line react-hooks/exhaustive-deps

  return null
}

export default React.memo(ImageLayer)
