import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import FireCenterDropdown from "./FireCenterDropdown";
import { FireCenter, FireShape } from "api/fbaAPI";

describe("FireCenterDropdown", () => {
  let fireCenters: FireCenter[];
  let setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  let setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;

  beforeEach(() => {
    fireCenters = [
      { id: 1, name: "Center A", stations: [] },
      { id: 2, name: "Center B", stations: [] },
    ];
    setSelectedFireCenter = vi.fn();
    setSelectedFireShape = vi.fn();
  });

  it("renders dropdown with options", () => {
    const { queryByTestId } = render(
      <FireCenterDropdown
        fireCenterOptions={fireCenters}
        selectedFireCenter={fireCenters[0]}
        setSelectedFireCenter={setSelectedFireCenter}
        setSelectedFireShape={setSelectedFireShape}
      />
    );
    const element = queryByTestId("fire-center-dropdown");
    expect(element).toHaveTextContent("Center A");
  });

  it("does not call setSelectedFireCenter if no option is selected", () => {
    render(
      <FireCenterDropdown
        fireCenterOptions={fireCenters}
        selectedFireCenter={undefined}
        setSelectedFireCenter={setSelectedFireCenter}
        setSelectedFireShape={setSelectedFireShape}
      />
    );

    expect(setSelectedFireCenter).not.toHaveBeenCalled();
  });

  it("changes selection and resets fire shape", async () => {
    render(
      <FireCenterDropdown
        fireCenterOptions={fireCenters}
        selectedFireCenter={fireCenters[0]}
        setSelectedFireCenter={setSelectedFireCenter}
        setSelectedFireShape={setSelectedFireShape}
      />
    );

    const user = userEvent.setup();
    const dropdown = screen.getByRole("combobox");
    await user.click(dropdown);

    const option = await screen.findByText("Center B");
    await user.click(option);

    expect(setSelectedFireShape).toHaveBeenCalledWith(undefined);
    expect(setSelectedFireCenter).toHaveBeenCalledWith(fireCenters[1]);
  });

  it("has instructional default text if no fire centre is selected", () => {
    render(
      <FireCenterDropdown
        fireCenterOptions={[]}
        selectedFireCenter={undefined}
        setSelectedFireCenter={setSelectedFireCenter}
        setSelectedFireShape={setSelectedFireShape}
      />
    );
    // Expect empty select to render with a zero width space.
    expect(screen.getByRole("combobox")).toHaveTextContent(
      "Select Fire Centre"
    );
  });
});
