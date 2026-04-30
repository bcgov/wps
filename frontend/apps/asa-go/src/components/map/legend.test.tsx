import { render, waitFor, within } from "@testing-library/react";
import Legend from "@/components/map/Legend";
import { HFI_LAYER_NAME, ZONE_STATUS_LAYER_NAME } from "@/layerDefinitions";
import { vi } from "vitest";
import { defaultLayerVisibility } from "@/components/map/layerVisibility";
import { userEvent } from "@testing-library/user-event";

describe("Legend", () => {
  const onLayerVisibilityChange = vi.fn();

  beforeEach(() => {
    onLayerVisibilityChange.mockClear();
  });

  it("renders the legend with defaults checked", async () => {
    const { getByTestId } = render(
      <Legend
        layerVisibility={defaultLayerVisibility}
        onLayerVisibilityChange={onLayerVisibilityChange}
      />
    );
    expect(getByTestId("asa-go-map-legend")).toBeInTheDocument();

    const zoneStatus = getByTestId("zone-checkbox");
    const zoneStatusCheckbox = within(zoneStatus).getByRole("checkbox");
    await waitFor(() => expect(zoneStatusCheckbox).toBeChecked());

    const hfi = getByTestId("hfi-checkbox");
    const hfiCheckbox = within(hfi).getByRole("checkbox");
    await waitFor(() => expect(hfiCheckbox).toBeChecked());
  });

  it("calls onLayerVisibilityChange when checkboxes are toggled", async () => {
    const { getByTestId } = render(
      <Legend
        layerVisibility={defaultLayerVisibility}
        onLayerVisibilityChange={onLayerVisibilityChange}
      />
    );
    const zoneCheckbox = getByTestId(`zone-checkbox`);
    const hfiCheckbox = getByTestId(`hfi-checkbox`);

    await userEvent.click(zoneCheckbox);
    await waitFor(() =>
      expect(onLayerVisibilityChange).toHaveBeenCalledWith(
        ZONE_STATUS_LAYER_NAME,
        false
      )
    );

    await userEvent.click(hfiCheckbox);
    await waitFor(() =>
      expect(onLayerVisibilityChange).toHaveBeenCalledWith(
        HFI_LAYER_NAME,
        false
      )
    );
  });
});
