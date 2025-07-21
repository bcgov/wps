// useFireCentreDetails.test.tsx
import { renderHook } from '@testing-library/react';
import { useFireCentreDetails } from './useFireCentreDetails';
import { FireCenter, FireShapeAreaDetail } from 'api/fbaAPI';
import { selectProvincialSummary } from '@/slices/provincialSummarySlice';
import { Provider } from 'react-redux';
import { configureStore, Store } from '@reduxjs/toolkit';
import { Mock, vi } from 'vitest';
import React from 'react';

// Mock the selector
vi.mock('@/slices/provincialSummarySlice', () => ({
  selectProvincialSummary: vi.fn(),
}));

// Helper to wrap hook with Redux provider
const createWrapper = (store: Store) => {
  return ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );
};

describe('useFireCentreDetails', () => {
  it('returns grouped and sorted fire shape details for a selected fire center', () => {
    const mockFireCenter: FireCenter = {
      id: 1,
      name: 'Test Centre',
      stations: [],
    };

    const mockSummary: Record<string, FireShapeAreaDetail[]> = {
      'Test Centre': [
        {
          fire_shape_id: 2,
          fire_shape_name: 'Zone B',
          fire_centre_name: 'Test Centre',
          combustible_area: 100,
          elevated_hfi_percentage: 10,
        },
        {
          fire_shape_id: 1,
          fire_shape_name: 'Zone A',
          fire_centre_name: 'Test Centre',
          combustible_area: 200,
          elevated_hfi_percentage: 20,
        },
        {
          fire_shape_id: 1,
          fire_shape_name: 'Zone A',
          fire_centre_name: 'Test Centre',
          combustible_area: 150,
          elevated_hfi_percentage: 15,
        },
      ],
    };

    // Mock selector return value
    ((selectProvincialSummary as unknown) as Mock).mockReturnValue(mockSummary);

    const store = configureStore({
      reducer: () => ({}), // dummy reducer
      preloadedState: {},
    });

    const { result } = renderHook(() => useFireCentreDetails(mockFireCenter), {
      wrapper: createWrapper(store),
    });

    expect(result.current).toEqual([
      {
        fire_shape_id: 1,
        fire_shape_name: 'Zone A',
        fire_centre_name: 'Test Centre',
        fireShapeDetails: [
          mockSummary['Test Centre'][1],
          mockSummary['Test Centre'][2],
        ],
      },
      {
        fire_shape_id: 2,
        fire_shape_name: 'Zone B',
        fire_centre_name: 'Test Centre',
        fireShapeDetails: [mockSummary['Test Centre'][0]],
      },
    ]);
  });

  it('returns an empty array if no fire center is selected', () => {
    ((selectProvincialSummary as unknown) as Mock).mockReturnValue({});
    const store = configureStore({ reducer: () => ({}) });

    const { result } = renderHook(() => useFireCentreDetails(undefined), {
      wrapper: createWrapper(store),
    });

    expect(result.current).toEqual([]);
  });
});
