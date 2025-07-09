import MapPopup from "@/components/map/MapPopup";
import ScaleContainer from "@/components/ScaleContainer";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
import {
  fireCentreLabelStyler,
  fireCentreLineStyler,
  fireShapeLabelStyler,
  fireShapeLineStyler,
  fireShapeStyler,
  hfiStyler,
} from "@/featureStylers";
import { fireZoneExtentsMap } from "@/fireZoneUnitExtents";
import {
  createBasemapLayer,
  createLocalBasemapVectorLayer,
  LOCAL_BASEMAP_LAYER_NAME,
} from "@/layerDefinitions";
import { selectFireShapeAreas, selectNetworkStatus } from "@/store";
import { CENTER_OF_BC } from "@/utils/constants";
import { PMTilesCache } from "@/utils/pmtilesCache";
import { PMTilesFileVectorSource } from "@/utils/pmtilesVectorSource";
import { Filesystem } from "@capacitor/filesystem";
import { Box } from "@mui/material";
import { FireShape, RunType } from "api/fbaAPI";
import { cloneDeep, isNull, isUndefined } from "lodash";
import { DateTime } from "luxon";
import { Map, MapBrowserEvent, Overlay, View } from "ol";
import { defaults as defaultControls } from "ol/control";
import ScaleLine from "ol/control/ScaleLine";
import { boundingExtent } from "ol/extent";
import TileLayer from "ol/layer/Tile";
import VectorTileLayer from "ol/layer/VectorTile";
import "ol/ol.css";
import { fromLonLat } from "ol/proj";
import React, { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import { BC_EXTENT, NavPanel } from "utils/constants";
export const MapContext = React.createContext<Map | null>(null);

const bcExtent = boundingExtent(BC_EXTENT.map((coord) => fromLonLat(coord)));

export interface FBAMapProps {
  testId?: string;
  selectedFireShape: FireShape | undefined;
  setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
  advisoryThreshold: number;
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
  setTab: React.Dispatch<React.SetStateAction<NavPanel>>;
}

const FBAMap = ({
  testId,
  selectedFireShape,
  setSelectedFireShape,
  advisoryThreshold,
  date,
  setDate,
  setTab,
}: FBAMapProps) => {
  const [map, setMap] = useState<Map | null>(null);
  const { networkStatus } = useSelector(selectNetworkStatus);
  const [scaleVisible, setScaleVisible] = useState<boolean>(true);
  const { fireShapeAreas } = useSelector(selectFireShapeAreas);
  const [basemapLayer] = useState<TileLayer>(createBasemapLayer());
  const [localBasemapVectorLayer, setLocalBasemapVectorLayer] =
    useState<VectorTileLayer>(() => {
      const layer = new VectorTileLayer();
      layer.set("name", LOCAL_BASEMAP_LAYER_NAME);
      return layer;
    });

  const [fireZoneFileLayer] = useState<VectorTileLayer>(
    new VectorTileLayer({
      style: fireShapeStyler(
        cloneDeep(fireShapeAreas),
        advisoryThreshold,
        true
      ),
      zIndex: 53,
      properties: { name: "fireZoneVector" },
    })
  );

  const [fireZoneHighlightFileLayer] = useState<VectorTileLayer>(
    new VectorTileLayer({
      style: fireShapeLineStyler(
        cloneDeep(fireShapeAreas),
        advisoryThreshold,
        selectedFireShape
      ),
      zIndex: 54,
      properties: { name: "fireZoneHighlightVector" },
    })
  );

  const mapRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;
  const scaleRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;
  const popupRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;

  const [popup, setPopup] = useState<Overlay>(
    new Overlay({
      autoPan: {
        animation: {
          duration: 250,
        },
      },
    })
  );

  const removeLayerByName = (map: Map, layerName: string) => {
    const layer = map
      .getLayers()
      .getArray()
      .find((l) => l.getProperties()?.name === layerName);
    if (layer) {
      map.removeLayer(layer);
    }
  };

  useEffect(() => {
    fireZoneFileLayer.setStyle(
      fireShapeStyler(cloneDeep(fireShapeAreas), advisoryThreshold, true)
    );
    fireZoneHighlightFileLayer.setStyle(
      fireShapeLineStyler(
        cloneDeep(fireShapeAreas),
        advisoryThreshold,
        selectedFireShape
      )
    );
    fireZoneFileLayer.changed();
    fireZoneHighlightFileLayer.changed();
  }, [fireShapeAreas]);

  useEffect(() => {
    if (!map) return;

    fireZoneHighlightFileLayer.setStyle(
      fireShapeLineStyler(
        cloneDeep(fireShapeAreas),
        advisoryThreshold,
        selectedFireShape
      )
    );

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFireShape]);

  useEffect(() => {
    // Toggle basemap visibility based on network connection status.
    if (networkStatus.connected === true) {
      localBasemapVectorLayer.setVisible(false);
      basemapLayer.setVisible(true);
    } else {
      basemapLayer.setVisible(false);
      localBasemapVectorLayer.setVisible(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [networkStatus]);

  useEffect(() => {
    // The locally cached basemap pmtiles layer loads async, so add it
    // to the map once it is loaded and state updated.
    if (isNull(map) || isNull(localBasemapVectorLayer)) {
      return;
    }
    if (networkStatus.connected) {
      localBasemapVectorLayer.setVisible(false);
    }
    // Remove the placeholder VTL and then add the new localBasemapVectorLayer
    removeLayerByName(map, LOCAL_BASEMAP_LAYER_NAME);
    map.addLayer(localBasemapVectorLayer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localBasemapVectorLayer]);

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type  HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return;

    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new Map({
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC),
      }),
      layers: [],
      overlays: [],
      controls: defaultControls({
        zoom: false,
      }),
    });
    mapObject.setTarget(mapRef.current);

    /******* Start scale line ******/

    const scaleBar = new ScaleLine({});
    scaleBar.setTarget(scaleRef.current);
    scaleBar.setMap(mapObject);

    const setScalelineVisibility = () => {
      setScaleVisible(true);
    };

    // Make the scale line visible when the user zooms in/out
    mapObject.getView().on("change:resolution", setScalelineVisibility);

    /******* End scale line ******/

    /******* Start map popup ******/
    const mapPopup = new Overlay({
      autoPan: {
        animation: {
          duration: 250,
        },
      },
      element: popupRef.current,
    });
    setPopup(mapPopup);
    mapPopup.setMap(mapObject);
    const mapClickHandler = (event: MapBrowserEvent<UIEvent>) => {
      fireZoneFileLayer.getFeatures(event.pixel).then((features) => {
        if (!features.length) {
          mapPopup.setPosition(undefined);
          return;
        }
        const feature = features[0];
        const zonePlacename = `${feature.getProperties().FIRE_ZONE_} - ${
          feature.getProperties().FIRE_ZON_1
        }`;
        const fireZone: FireShape = {
          fire_shape_id: feature.getProperties().OBJECTID,
          mof_fire_zone_name: zonePlacename,
          mof_fire_centre_name: feature.getProperties().FIRE_CENTR,
          area_sqm: feature.getProperties().Shape_Area,
        };
        mapPopup.setPosition(event.coordinate);
        setSelectedFireShape(fireZone);
      });
    };
    mapObject.on("singleclick", mapClickHandler);

    /******* End map popup ******/

    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] });

    setMap(mapObject);

    const loadPMTiles = async () => {
      // TODO make for date, run type, run date configurable from UI
      const hfiVectorSource = await PMTilesFileVectorSource.createHFILayer(
        new PMTilesCache(Filesystem),
        {
          filename: "hfi.pmtiles",
          for_date: DateTime.fromFormat("2024/08/08", "yyyy/MM/dd"),
          run_type: RunType.FORECAST,
          run_date: DateTime.fromFormat("2024/08/08", "yyyy/MM/dd"),
        }
      );

      const fireCentresSource = await PMTilesFileVectorSource.createStaticLayer(
        new PMTilesCache(Filesystem),
        {
          filename: "fireCentres.pmtiles",
        }
      );

      const fireCentreLabelVectorSource =
        await PMTilesFileVectorSource.createStaticLayer(
          new PMTilesCache(Filesystem),
          {
            filename: "fireCentreLabels.pmtiles",
          }
        );

      const fireZoneSource = await PMTilesFileVectorSource.createStaticLayer(
        new PMTilesCache(Filesystem),
        {
          filename: "fireZoneUnits.pmtiles",
        }
      );
      fireZoneFileLayer.setSource(fireZoneSource);
      fireZoneHighlightFileLayer.setSource(fireZoneSource);

      const fireZoneLabelVectorSource =
        await PMTilesFileVectorSource.createStaticLayer(
          new PMTilesCache(Filesystem),
          {
            filename: "fireZoneUnitLabels.pmtiles",
          }
        );
      if (mapObject) {
        const fireCentreFileLayer = new VectorTileLayer({
          source: fireCentresSource,
          style: fireCentreLineStyler(undefined),
          zIndex: 52,
        });

        const fireCentreLabelsFileLayer = new VectorTileLayer({
          source: fireCentreLabelVectorSource,
          style: fireCentreLabelStyler,
          zIndex: 100,
          maxZoom: 6,
        });

        const fireZoneLabelFileLayer = new VectorTileLayer({
          source: fireZoneLabelVectorSource,
          declutter: true,
          style: fireShapeLabelStyler(selectedFireShape),
          zIndex: 99,
          minZoom: 6,
        });

        const hfiFileLayer = new VectorTileLayer({
          source: hfiVectorSource,
          style: hfiStyler,
          zIndex: 52,
        });

        const localBasemapLayer = await createLocalBasemapVectorLayer();
        setLocalBasemapVectorLayer(localBasemapLayer);

        mapObject.addLayer(basemapLayer);
        mapObject.addLayer(hfiFileLayer);
        mapObject.addLayer(fireCentreFileLayer);
        mapObject.addLayer(fireCentreLabelsFileLayer);
        mapObject.addLayer(fireZoneFileLayer);
        mapObject.addLayer(fireZoneHighlightFileLayer);
        mapObject.addLayer(fireZoneLabelFileLayer);
      }
    };
    loadPMTiles();

    return () => {
      mapObject.getView().un("change:resolution", setScalelineVisibility);
      mapObject.un("click", mapClickHandler);
      mapObject.setTarget("");
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handlePopupClose = () => {
    popup.setPosition(undefined);
  };

  const handleZoomToSelectedFireShape = () => {
    if (isNull(map)) {
      return;
    }
    if (selectedFireShape) {
      const zoneExtent = fireZoneExtentsMap.get(
        selectedFireShape.fire_shape_id.toString()
      );
      if (!isUndefined(zoneExtent)) {
        map.getView().fit(zoneExtent, {
          duration: 400,
          padding: [100, 100, 100, 100],
          maxZoom: 8,
        });
      }
    }
    popup.setPosition(undefined);
  };

  return (
    <MapContext.Provider value={map}>
      <Box
        ref={mapRef}
        data-testid={testId}
        sx={{
          display: "flex",
          flex: 1,
          position: "relative",
        }}
      >
        <Box
          sx={{ position: "absolute", left: "8px", bottom: "8px", zIndex: 1 }}
        >
          <TodayTomorrowSwitch date={date} setDate={setDate} />
        </Box>
        <ScaleContainer
          visible={scaleVisible}
          setVisible={setScaleVisible}
          ref={scaleRef}
        />
        <MapPopup
          ref={popupRef}
          selectedFireShape={selectedFireShape}
          onClose={handlePopupClose}
          onSelectProfile={() => setTab(NavPanel.PROFILE)}
          onSelectReport={() => setTab(NavPanel.ADVISORY)}
          onSelectZoom={handleZoomToSelectedFireShape}
        />
      </Box>
    </MapContext.Provider>
  );
};

export default React.memo(FBAMap);
