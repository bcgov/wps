import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import FireCenterDropdown from "./FireCenterDropdown";
import { FireShape } from "api/fbaAPI";
import type { FireCentre } from "@/types/fireCentre";

describe("FireCenterDropdown", () => {
  let fireCentres: FireCentre[];
  let setSelectedFireCentre: React.Dispatch<
    React.SetStateAction<FireCentre | undefined>
  >;
  let setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;

  beforeEach(() => {
    fireCentres = [
      { id: 1, name: "Center A" },
      { id: 2, name: "Center B" },
    ];
    setSelectedFireCentre = vi.fn();
    setSelectedFireShape = vi.fn();
  });

  it("renders dropdown with options", () => {
    const { queryByTestId } = render(
      <FireCenterDropdown
        fireCentreOptions={fireCentres}
        selectedFireCentre={fireCentres[0]}
        setSelectedFireCentre={setSelectedFireCentre}
        setSelectedFireShape={setSelectedFireShape}
      />,
    );
    const element = queryByTestId("fire-center-dropdown");
    expect(element).toHaveTextContent("Center A");
  });

  it("does not call setSelectedFireCentre if no option is selected", () => {
    render(
      <FireCenterDropdown
        fireCentreOptions={fireCentres}
        selectedFireCentre={undefined}
        setSelectedFireCentre={setSelectedFireCentre}
        setSelectedFireShape={setSelectedFireShape}
      />,
    );

    expect(setSelectedFireCentre).not.toHaveBeenCalled();
  });

  it("changes selection and resets fire shape", async () => {
    render(
      <FireCenterDropdown
        fireCentreOptions={fireCentres}
        selectedFireCentre={fireCentres[0]}
        setSelectedFireCentre={setSelectedFireCentre}
        setSelectedFireShape={setSelectedFireShape}
      />,
    );

    const user = userEvent.setup();
    const dropdown = screen.getByRole("combobox");
    await user.click(dropdown);

    const option = await screen.findByText("Center B");
    await user.click(option);

    expect(setSelectedFireShape).toHaveBeenCalledWith(undefined);
    expect(setSelectedFireCentre).toHaveBeenCalledWith(fireCentres[1]);
  });

  it("has instructional default text if no fire centre is selected", () => {
    render(
      <FireCenterDropdown
        fireCentreOptions={[]}
        selectedFireCentre={undefined}
        setSelectedFireCentre={setSelectedFireCentre}
        setSelectedFireShape={setSelectedFireShape}
      />,
    );
    expect(
      screen.getByRole("combobox", { name: /centre/i }),
    ).toBeInTheDocument();
  });

  it("does not show 'Fire Centre' in the selected value", () => {
    const selectedFireCentre: FireCentre = {
      id: 3,
      name: "Kamloops Fire Centre",
    };

    render(
      <FireCenterDropdown
        fireCentreOptions={[selectedFireCentre]}
        selectedFireCentre={selectedFireCentre}
        setSelectedFireCentre={setSelectedFireCentre}
        setSelectedFireShape={setSelectedFireShape}
      />,
    );

    const dropdown = screen.getByTestId("fire-center-dropdown");
    expect(dropdown).toHaveTextContent("Kamloops");
    expect(dropdown).not.toHaveTextContent("Fire Centre");
  });
});
