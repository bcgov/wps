import { centerOnFireShape } from "@/components/map/fireShapeCentering";
import {
  defaultLayerVisibility,
  LayerVisibility,
  loadLayerVisibility,
  saveLayerVisibility,
  setDefaultLayerVisibility,
  setZoneStatusLayerVisibility,
} from "@/components/map/layerVisibility";
import LegendPopover from "@/components/map/LegendPopover";
import UserLocationIndicator from "@/components/map/LocationIndicator";
import MapPopup from "@/components/map/MapPopup";
import { loadMapViewState, saveMapViewState } from "@/components/map/mapView";
import ScaleContainer from "@/components/map/ScaleContainer";
import MapIconButton from "@/components/MapIconButton";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
import { MapContext } from "@/context/MapContext";
import {
  fireCentreLabelStyler,
  fireCentreLineStyler,
  fireShapeLabelStyler,
  fireShapeLineStyler,
  fireShapeStyler,
} from "@/featureStylers";
import { fireZoneExtentsMap } from "@/fireZoneUnitExtents";
import { useFireShapeAreasForDate } from "@/hooks/dataHooks";
import { useRunParameterForDate } from "@/hooks/useRunParameterForDate";
import {
  BASEMAP_LAYER_NAME,
  createBasemapLayer,
  createHFILayer,
  createLocalBasemapVectorLayer,
  HFI_LAYER_NAME,
  LOCAL_BASEMAP_LAYER_NAME,
  ZONE_STATUS_LAYER_NAME,
} from "@/layerDefinitions";
import { startWatchingLocation } from "@/slices/geolocationSlice";
import { NavPanel } from "@/utils/constants";
import { AppDispatch, selectGeolocation, selectNetworkStatus } from "@/store";
import { PMTilesCache } from "@/utils/pmtilesCache";
import { PMTilesFileVectorSource } from "@/utils/pmtilesVectorSource";
import { Filesystem } from "@capacitor/filesystem";
import GpsOffIcon from "@mui/icons-material/GpsOff";
import LayersIcon from "@mui/icons-material/Layers";
import MyLocationIcon from "@mui/icons-material/MyLocation";
import { Box } from "@mui/material";
import { FireCenter, FireShape } from "api/fbaAPI";
import { cloneDeep, isNil, isNull, isUndefined } from "lodash";
import { DateTime } from "luxon";
import { Map, MapBrowserEvent, Overlay, View } from "ol";
import { defaults as defaultControls } from "ol/control";
import ScaleLine from "ol/control/ScaleLine";
import { boundingExtent } from "ol/extent";
import { defaults as defaultInteractions } from "ol/interaction";
import VectorTileLayer from "ol/layer/VectorTile";
import "ol/ol.css";
import { fromLonLat } from "ol/proj";
import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { BC_EXTENT } from "utils/constants";

// used for setting the initial map extent
const bcExtent = boundingExtent(BC_EXTENT.map((coord) => fromLonLat(coord)));

// used for bounding the map extent, limit panning to BC + buffer
const buffer = 1_500_000;
const BC_FULL_MAP_EXTENT_3857 = [
  bcExtent[0] - buffer,
  bcExtent[1] - buffer,
  bcExtent[2] + buffer,
  bcExtent[3] + buffer,
];

export interface ASAGoMapProps {
  testId: string;
  selectedFireShape: FireShape | undefined;
  setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
  setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  advisoryThreshold: number;
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
  setTab: React.Dispatch<React.SetStateAction<NavPanel>>;
}

const ASAGoMap = ({
  testId,
  selectedFireShape,
  setSelectedFireShape,
  setSelectedFireCenter,
  advisoryThreshold,
  date,
  setDate,
  setTab,
}: ASAGoMapProps) => {
  const dispatch: AppDispatch = useDispatch();

  // selectors & hooks
  const { position, error, loading } = useSelector(selectGeolocation);
  const { networkStatus } = useSelector(selectNetworkStatus);

  // hooks
  const fireShapeAreas = useFireShapeAreasForDate(date);
  const runParameter = useRunParameterForDate(date);

  // state
  const [map, setMap] = useState<Map | null>(null);
  const [scaleVisible, setScaleVisible] = useState<boolean>(true);
  const [basemapLayer, setBasemapLayer] = useState<VectorTileLayer | null>(
    null
  );
  const [localBasemapVectorLayer, setLocalBasemapVectorLayer] =
    useState<VectorTileLayer | null>(null);
  const [centerOnLocation, setCenterOnLocation] = useState<boolean>(false);
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>(
    defaultLayerVisibility
  );
  const [legendAnchorEl, setLegendAnchorEl] =
    useState<HTMLButtonElement | null>(null);

  const [fireZoneFileLayer] = useState<VectorTileLayer>(
    new VectorTileLayer({
      style: fireShapeStyler(
        cloneDeep(fireShapeAreas),
        advisoryThreshold,
        layerVisibility[ZONE_STATUS_LAYER_NAME]
      ),
      zIndex: 53,
      properties: { name: ZONE_STATUS_LAYER_NAME },
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

  const toggleLayersRef = useRef<Record<string, VectorTileLayer | null>>({});

  const mapRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;
  const scaleRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;
  const popupRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;
  const clickSourceRef = useRef<boolean>(false);

  const [popup] = useState<Overlay>(
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

  const replaceMapLayer = React.useCallback(
    (layerName: string, layer: VectorTileLayer | null) => {
      if (!map) return;
      if (toggleLayersRef.current[layerName]) {
        map.removeLayer(toggleLayersRef.current[layerName]);
      }
      if (layer) {
        map.addLayer(layer);
      }
      toggleLayersRef.current[layerName] = layer;
    },
    [map]
  );

  /**
   *
   * - If location tracking is not active, dispatches an action to start tracking.
   * - Sets a flag to center the map on the user's location upon update.
   * - If location tracking is already active and we have a position,
   *   it centers the map on the user's current position.
   */
  const handleLocationButtonClick = async () => {
    if (!map) return;

    if (!position || error) {
      dispatch(startWatchingLocation());
      setCenterOnLocation(true); // center map when position arrives
      return;
    }
    const pos = fromLonLat([
      position.coords.longitude,
      position.coords.latitude,
    ]);
    map.getView().animate({
      center: pos,
      zoom: 7.5,
      duration: 1000,
    });
  };

  const handleLegendButtonClick = (
    event: React.MouseEvent<HTMLButtonElement>
  ) => {
    setLegendAnchorEl(event.currentTarget);
  };

  const handleLegendClose = () => {
    setLegendAnchorEl(null);
  };

  useEffect(() => {
    const fetchVisibility = async () => {
      const loaded = await loadLayerVisibility(defaultLayerVisibility);
      setLayerVisibility(loaded);
    };
    fetchVisibility();
  }, []);

  useEffect(() => {
    saveLayerVisibility(layerVisibility);
  }, [layerVisibility]);

  // center map when position is updated after requesting location
  useEffect(() => {
    if (centerOnLocation && position && map) {
      const pos = fromLonLat([
        position.coords.longitude,
        position.coords.latitude,
      ]);
      map.getView().animate({
        center: pos,
        zoom: 7.5,
        duration: 1000,
      });
      setCenterOnLocation(false); // Reset flag
    }
  }, [centerOnLocation, position, map]);

  useEffect(() => {
    fireZoneFileLayer.setStyle(
      fireShapeStyler(
        cloneDeep(fireShapeAreas),
        advisoryThreshold,
        layerVisibility[ZONE_STATUS_LAYER_NAME]
      )
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

    // Only center if the change didn't come from a click
    if (!clickSourceRef.current) {
      centerOnFireShape(map, selectedFireShape, fireZoneExtentsMap, popup);
    }

    // Reset the flag for next change
    clickSourceRef.current = false;

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFireShape]);

  useEffect(() => {
    // Toggle basemap visibility based on network connection status.
    if (isNil(map)) {
      return;
    }
    removeLayerByName(map, BASEMAP_LAYER_NAME);
    if (networkStatus.connected === true) {
      localBasemapVectorLayer?.setVisible(false);
      if (!isNil(basemapLayer)) {
        map.addLayer(basemapLayer);
      }
    } else {
      localBasemapVectorLayer?.setVisible(true);
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
        extent: BC_FULL_MAP_EXTENT_3857, // constrains panning
      }),
      layers: [],
      overlays: [],
      controls: defaultControls({
        zoom: false,
      }),
      interactions: defaultInteractions({
        doubleClickZoom: true,
      }),
    });
    mapObject.setTarget(mapRef.current);

    /******* Start scale line ******/

    const scaleBar = new ScaleLine({});
    scaleBar.setTarget(scaleRef.current);
    mapObject.addControl(scaleBar);
    const setScalelineVisibility = () => {
      setScaleVisible(true);
    };

    // Make the scale line visible when the user zooms in/out
    mapObject.getView().on("change:resolution", setScalelineVisibility);

    /******* End scale line ******/

    /******* Start map popup ******/
    popup.setElement(popupRef.current);
    mapObject.addOverlay(popup);
    const mapClickHandler = (event: MapBrowserEvent<UIEvent>) => {
      fireZoneFileLayer.getFeatures(event.pixel).then((features) => {
        clickSourceRef.current = true; // Mark as click source
        if (!features.length) {
          popup.setPosition(undefined);
          setSelectedFireCenter(undefined);
          setSelectedFireShape(undefined);
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
        popup.setPosition(event.coordinate);
        setSelectedFireShape(fireZone);
      });
    };
    mapObject.on("singleclick", mapClickHandler);

    /******* End map popup ******/

    setMap(mapObject);

    const loadPMTiles = async () => {
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

        const localBasemapLayer = await createLocalBasemapVectorLayer();
        setLocalBasemapVectorLayer(localBasemapLayer);

        const basemapLayer = await createBasemapLayer();
        setBasemapLayer(basemapLayer);

        mapObject.addLayer(basemapLayer);
        mapObject.addLayer(fireCentreFileLayer);
        mapObject.addLayer(fireCentreLabelsFileLayer);
        mapObject.addLayer(fireZoneFileLayer);
        mapObject.addLayer(fireZoneHighlightFileLayer);
        mapObject.addLayer(fireZoneLabelFileLayer);
      }
    };
    loadPMTiles();

    return () => {
      mapObject.removeControl(scaleBar);
      mapObject.un("click", mapClickHandler);
      mapObject.getView().un("change:resolution", setScalelineVisibility);
      mapObject.setTarget("");
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // map state storage and restoration
  useEffect(() => {
    if (!map) return;
    (async () => {
      const savedState = await loadMapViewState();
      if (savedState) {
        map.getView().setZoom(savedState.zoom);
        map.getView().setCenter(savedState.center);
      } else {
        map.getView().fit(bcExtent, { padding: [50, 50, 50, 50] });
      }
    })();

    const saveStateHandler = () => {
      const view = map.getView();
      const zoom = view.getZoom();
      const center = view.getCenter();
      if (zoom && center) {
        saveMapViewState({
          zoom,
          center,
        });
      }
    };
    map.on("moveend", saveStateHandler);

    return () => {
      map.un("moveend", saveStateHandler);
    };
  }, [map]);

  useEffect(() => {
    if (!map) return;

    (async () => {
      let hfiLayer: VectorTileLayer | null = null;
      if (
        !isNil(runParameter?.run_type) &&
        !isNil(runParameter?.run_datetime)
      ) {
        hfiLayer = await createHFILayer(
          {
            filename: "hfi.pmtiles",
            for_date: date,
            run_type: runParameter.run_type,
            run_date: DateTime.fromISO(runParameter.run_datetime),
          },
          layerVisibility[HFI_LAYER_NAME]
        );
      }
      replaceMapLayer(HFI_LAYER_NAME, hfiLayer);
    })();
  }, [map, runParameter, date, layerVisibility, replaceMapLayer]);

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
          padding: [50, 50, 50, 50],
          maxZoom: 10,
        });
      }
    }
    popup.setPosition(undefined);
  };

  const handleLayerVisibilityChange = (
    layerName: string,
    visible: boolean
  ): void => {
    setLayerVisibility((prev) => ({
      ...prev,
      [layerName]: visible,
    }));

    // The Zone Status layer is unique because it's always visible, but we'll change it's style
    // so it isn't filled in anymore if it's "off".
    if (layerName === ZONE_STATUS_LAYER_NAME) {
      setZoneStatusLayerVisibility(
        fireZoneFileLayer,
        fireShapeAreas,
        advisoryThreshold,
        visible
      );
    } else {
      setDefaultLayerVisibility(toggleLayersRef.current, layerName, visible);
    }
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
          backgroundColor: "grey.300",
        }}
      >
        <UserLocationIndicator map={map} position={position} error={error} />

        <Box
          sx={{
            position: "absolute",
            left: "8px",
            bottom: "8px",
            zIndex: 2,
            display: "flex",
            flexDirection: "column",
            gap: 1,
          }}
        >
          <MapIconButton
            onClick={handleLegendButtonClick}
            icon={<LayersIcon />}
            testid="legend-toggle-button"
          />
          <MapIconButton
            onClick={handleLocationButtonClick}
            icon={error ? <GpsOffIcon color="error" /> : <MyLocationIcon />}
            testid="location-button"
            loading={loading}
          />
          <TodayTomorrowSwitch date={date} setDate={setDate} />
        </Box>

        <LegendPopover
          anchorEl={legendAnchorEl}
          onClose={handleLegendClose}
          layerVisibility={layerVisibility}
          onLayerVisibilityChange={handleLayerVisibilityChange}
        />

        <ScaleContainer
          visible={scaleVisible}
          setVisible={setScaleVisible}
          ref={scaleRef}
        />
        <MapPopup
          ref={popupRef}
          selectedFireShape={selectedFireShape}
          onClose={handlePopupClose}
          onSelectProfile={() => {
            setTab(NavPanel.PROFILE);
            handlePopupClose();
          }}
          onSelectReport={() => {
            setTab(NavPanel.ADVISORY);
            handlePopupClose();
          }}
          onSelectZoom={handleZoomToSelectedFireShape}
        />
      </Box>
    </MapContext.Provider>
  );
};

export default React.memo(ASAGoMap);
