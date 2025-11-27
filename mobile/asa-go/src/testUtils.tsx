import { RootState } from "@/store";
import { configureStore } from "@reduxjs/toolkit";

import { rootReducer } from "@/rootReducer";
import { vi } from "vitest";

export const createTestStore = (initialState: Partial<RootState> = {}) => {
  return configureStore({
    reducer: rootReducer,
    preloadedState: {
      ...initialState,
    },
  });
};

export const baseLayerMock = {
  set: vi.fn(),
  setStyle: vi.fn(),
  changed: vi.fn(),
  getProperties: vi.fn(() => ({})),
  setVisible: vi.fn(),
  setSource: vi.fn(),
  on: vi.fn(),
  un: vi.fn(),
  once: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
};

export const createLayerMock = (name: string) => {
  return {
    set: vi.fn(),
    setStyle: vi.fn(),
    changed: vi.fn(),
    getProperties: vi.fn(() => ({ name })),
    setVisible: vi.fn(),
    setSource: vi.fn(),
    on: vi.fn(),
    un: vi.fn(),
    once: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
};

export const setupOpenLayersMocks = () => {
  vi.mock("ol/Map", () => {
    const layers: unknown[] = [];
    return {
      default: vi.fn().mockImplementation(() => ({
        setTarget: vi.fn(),
        getView: vi.fn(() => ({
          animate: vi.fn(),
        })),
        addLayer: vi.fn(),
        getLayers: vi.fn(() => ({
          getArray: vi.fn(() => layers),
        })),
        on: vi.fn(),
        un: vi.fn(),
        once: vi.fn(),
        removeLayer: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    };
  });

  vi.mock("ol/layer/VectorTile", () => ({
    default: vi.fn().mockImplementation(() => ({ ...baseLayerMock })),
  }));

  vi.mock("ol/layer/Tile", () => ({
    default: vi.fn().mockImplementation(() => ({ ...baseLayerMock })),
  }));

  vi.mock("ol/Overlay", () => ({
    default: vi.fn().mockImplementation(() => ({
      setPosition: vi.fn(),
      getElement: vi.fn(),
    })),
  }));

  vi.mock("ol-mapbox-style", () => ({
    applyStyle: vi.fn(),
  }));
};
