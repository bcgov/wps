import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import NotificationErrorSnackbar from "./NotificationErrorSnackbar";

describe("NotificationErrorSnackbar", () => {
  it("renders the message when open", () => {
    render(
      <NotificationErrorSnackbar
        open={true}
        onClose={vi.fn()}
        message="Something went wrong"
      />,
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <NotificationErrorSnackbar
        open={false}
        onClose={vi.fn()}
        message="Something went wrong"
      />,
    );
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("renders with error severity", () => {
    render(
      <NotificationErrorSnackbar
        open={true}
        onClose={vi.fn()}
        message="Something went wrong"
      />,
    );
    expect(screen.getByRole("alert")).toHaveClass("MuiAlert-colorError");
  });

  it("calls onClose when the close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <NotificationErrorSnackbar
        open={true}
        onClose={onClose}
        message="Something went wrong"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /close/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
