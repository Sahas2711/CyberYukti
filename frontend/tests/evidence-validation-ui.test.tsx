import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { EvidencePanel } from "@/components/case/EvidencePanel";
import type { ValidationResult } from "@/lib/api/types";

function mockConfirmedEvidence(): ValidationResult {
  return {
    cluster_id: "CLUSTER-TEST-001",
    status: "CONFIRMED",
    confidence: 0.95,
    observations: [
      {
        observation_id: "obs-test-01",
        type: "package_version",
        target: "package.json > jquery",
        observed_value: "1.12.4 (vulnerable)",
        expected_value: ">=3.5.0",
        method: "package_version",
      },
    ],
    validated_at: "2026-09-11T12:00:00Z",
    validator_version: "2.1.0",
  };
}

function mockNotConfirmedEvidence(): ValidationResult {
  return {
    cluster_id: "CLUSTER-TEST-002",
    status: "NOT_CONFIRMED",
    confidence: 0.88,
    observations: [
      {
        observation_id: "obs-test-02",
        type: "package_version",
        target: "package.json > jquery",
        observed_value: "3.6.0 (patched)",
        expected_value: "<3.5.0",
        method: "package_version",
      },
    ],
    validated_at: "2026-09-11T12:30:00Z",
    validator_version: "2.1.0",
  };
}

describe("EvidencePanel Live Probe UI", () => {
  it("renders live probe button and target selector when onValidate is passed", () => {
    const onValidate = vi.fn();
    render(
      <EvidencePanel
        evidence={mockConfirmedEvidence()}
        onValidate={onValidate}
      />
    );

    const button = screen.getByRole("button", { name: /run live probe/i });
    expect(button).toBeDefined();

    const select = screen.getByLabelText(/validation probe target/i);
    expect(select).toBeDefined();
  });

  it("triggers onValidate with undefined (default target) when default option is selected", () => {
    const onValidate = vi.fn();
    render(
      <EvidencePanel
        evidence={mockConfirmedEvidence()}
        onValidate={onValidate}
      />
    );

    const button = screen.getByRole("button", { name: /run live probe/i });
    fireEvent.click(button);

    expect(onValidate).toHaveBeenCalledTimes(1);
    expect(onValidate).toHaveBeenCalledWith(undefined);
  });

  it("triggers onValidate with chosen target override when target is changed", () => {
    const onValidate = vi.fn();
    render(
      <EvidencePanel
        evidence={mockConfirmedEvidence()}
        onValidate={onValidate}
      />
    );

    const select = screen.getByLabelText(/validation probe target/i);
    fireEvent.change(select, { target: { value: "shop-api-01-patched" } });

    const button = screen.getByRole("button", { name: /run live probe/i });
    fireEvent.click(button);

    expect(onValidate).toHaveBeenCalledWith("shop-api-01-patched");
  });

  it("shows disabled probing state while validating is true", () => {
    const onValidate = vi.fn();
    render(
      <EvidencePanel
        evidence={mockConfirmedEvidence()}
        onValidate={onValidate}
        validating={true}
      />
    );

    const button = screen.getByRole("button", { name: /probing/i });
    expect(button).toBeDefined();
    expect(button.hasAttribute("disabled")).toBe(true);
  });

  it("displays contradiction banner and expected vs observed for NOT_CONFIRMED", () => {
    render(<EvidencePanel evidence={mockNotConfirmedEvidence()} />);

    expect(
      screen.getByText(/Contradiction detected — scanner claim not confirmed/i)
    ).toBeDefined();
    expect(screen.getAllByText("3.6.0 (patched)").length).toBeGreaterThanOrEqual(1);
  });
});
