import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DateTime } from "luxon";
import InfoBar from "./InfoBar";
import { StatusEnum } from "@/utils/constants";

const viewingDate = DateTime.fromISO("2024-07-15");

describe("InfoBar", () => {
  it("renders viewing date in correct format", () => {
    render(
      <InfoBar
        lastUpdated={null}
        viewingDate={viewingDate}
        status={StatusEnum.INFO}
        Icon="icon.svg"
      />,
    );
    expect(screen.getByText(/Mon, Jul 15\./)).toBeInTheDocument();
  });

  it("renders last updated date when provided", () => {
    render(
      <InfoBar
        lastUpdated="2024-07-15T14:30:00"
        viewingDate={viewingDate}
        status={StatusEnum.INFO}
        Icon="icon.svg"
      />,
    );
    expect(screen.getByText(/Updated: Jul 15,/)).toBeInTheDocument();
  });

  it("renders n/a when lastUpdated is null", () => {
    render(
      <InfoBar
        lastUpdated={null}
        viewingDate={viewingDate}
        status={StatusEnum.INFO}
        Icon="icon.svg"
      />,
    );
    expect(screen.getByText(/Updated: n\/a\./)).toBeInTheDocument();
  });

  it("renders statusText when provided", () => {
    render(
      <InfoBar
        lastUpdated={null}
        viewingDate={viewingDate}
        status={StatusEnum.WARNING}
        Icon="icon.svg"
        statusText="Offline mode"
      />,
    );
    expect(screen.getByText(/Offline mode/)).toBeInTheDocument();
  });

  it("does not render statusText when omitted", () => {
    render(
      <InfoBar
        lastUpdated={null}
        viewingDate={viewingDate}
        status={StatusEnum.INFO}
        Icon="icon.svg"
      />,
    );
    expect(screen.queryByText(/Offline mode/)).not.toBeInTheDocument();
  });

  it("renders an img with the correct src", () => {
    render(
      <InfoBar
        lastUpdated={null}
        viewingDate={viewingDate}
        status={StatusEnum.INFO}
        Icon="network-icon.svg"
      />,
    );
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("src", "network-icon.svg");
  });

  it("renders Viewing: label", () => {
    render(
      <InfoBar
        lastUpdated={null}
        viewingDate={viewingDate}
        status={StatusEnum.INFO}
        Icon="icon.svg"
      />,
    );
    expect(screen.getByText("Viewing:")).toBeInTheDocument();
  });
});
