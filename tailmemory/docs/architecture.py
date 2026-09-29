from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def box(ax, x: float, y: float, title: str, body: str, color: str) -> None:
    patch = FancyBboxPatch(
        (x, y),
        2.7,
        1.15,
        boxstyle="round,pad=0.03,rounding_size=0.04",
        linewidth=1.4,
        edgecolor=color,
        facecolor="#f8fafc",
    )
    ax.add_patch(patch)
    ax.text(x + 0.12, y + 0.82, title, fontsize=11, weight="bold", color=color)
    ax.text(x + 0.12, y + 0.55, body, fontsize=8.5, va="top", linespacing=1.45)


def main() -> None:
    output = Path(__file__).resolve().parent / "architecture.png"
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.4)
    ax.axis("off")
    ax.text(0.2, 4.85, "TailMemory architecture", fontsize=18, weight="bold")
    ax.text(
        0.2,
        4.48,
        "Aircraft-scoped persistent memory + structured advisory generation",
        fontsize=10,
        color="#475569",
    )
    box(ax, 0.2, 2.45, "Streamlit UI", "tail selection\nfault + feedback loop", "#0b7285")
    box(ax, 3.35, 2.45, "HindsightClient", "retain / recall\nexact tail tag scope", "#7c3aed")
    box(ax, 6.5, 2.45, "Hindsight Cloud", "persistent memory\nsemantic recall", "#7c3aed")
    box(ax, 3.35, 0.65, "DiagnosisAgent", "Groq JSON schema\nPydantic validation", "#d9480f")
    box(ax, 6.5, 0.65, "Synthetic data", "8 tails / held-out faults\nFAA vocabulary sample", "#2f9e44")
    box(ax, 9.65, 2.45, "Qualified human", "reviews advisory\nrecords outcome", "#495057")
    for start, end in [
        ((2.9, 3.02), (3.35, 3.02)),
        ((6.05, 3.02), (6.5, 3.02)),
        ((4.7, 2.45), (4.7, 1.8)),
        ((7.85, 1.8), (7.85, 2.45)),
        ((9.2, 3.02), (9.65, 3.02)),
    ]:
        ax.annotate(
            "",
            xy=end,
            xytext=start,
            arrowprops={"arrowstyle": "->", "color": "#64748b", "linewidth": 1.4},
        )
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()