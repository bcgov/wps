import { Box } from '@mui/material';
import React, { useEffect, useRef, useState } from 'react';
import { Map, View } from 'ol';
import { fromLonLat } from 'ol/proj';
import 'ol/ol.css';
import { createVectorTileLayer, getStyleJson } from '@/utils/vectorLayerUtils';
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@/utils/env';
import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions';
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants';
import { boundingExtent } from 'ol/extent';

export const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const SMURFIMap = () => {
  const [map, setMap] = useState<Map | null>(null);
  const mapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!mapRef.current) return;

    const mapObject = new Map({
      target: mapRef.current,
      layers: [], // known-good baseline
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })

    setMap(mapObject);

    const loadBaseMap = async () => {
      const style = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, style, 1, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }
    loadBaseMap()

    return () => {
      mapObject.setTarget('');
    };
  }, []);

  return (
    <MapContext.Provider value={map}>
      <Box  sx={{ position: 'relative', width: '100%', height: '100%', minHeight: 0, flex: 1}}>
        <Box ref={mapRef} data-testid={'smurfi-map'} sx={{ width: '100%', height: '100%' }} />
      </Box>
    </MapContext.Provider>
  );
};

export default SMURFIMap;
