import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Moufida — your 24/7 AI co-founder";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OG() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px",
          background: "linear-gradient(135deg, #F8F0E4 0%, #F5EBDD 45%, #EFE0CC 100%)",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: 18,
              background: "linear-gradient(135deg,#C96A2D,#6F4E37)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#F5EBDD",
              fontSize: 40,
              fontWeight: 800,
            }}
          >
            M
          </div>
          <span style={{ fontSize: 40, fontWeight: 800, color: "#2C1E17" }}>Moufida</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              fontSize: 76,
              fontWeight: 800,
              color: "#2C1E17",
              lineHeight: 1.05,
              maxWidth: 1000,
            }}
          >
            <span style={{ marginRight: 22 }}>Your 24/7 AI</span>
            <span style={{ marginRight: 22, color: "#C96A2D" }}>co-founder</span>
            <span>that never sleeps</span>
          </div>
          <div style={{ fontSize: 32, color: "#8B6E5A", maxWidth: 920, lineHeight: 1.35 }}>
            Diagnose, score &amp; roadmap your startup. Full AI due diligence + competitor deep-search. 100% local.
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div
            style={{
              background: "#C96A2D",
              color: "#F5EBDD",
              fontSize: 28,
              fontWeight: 700,
              padding: "14px 28px",
              borderRadius: 14,
              display: "flex",
            }}
          >
            Join the waitlist →
          </div>
          <span style={{ fontSize: 26, color: "#8B6E5A" }}>Launching June 28, 2026</span>
        </div>
      </div>
    ),
    { ...size }
  );
}
