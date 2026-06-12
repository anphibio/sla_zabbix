import React, { type ReactNode } from "react";

type AppLayoutProps = {
  currentSection: string;
  children: ReactNode;
};

const shellStyle = {
  minHeight: "100vh",
  padding: "32px",
  backgroundColor: "#0f172a",
  color: "#e2e8f0",
  fontFamily: "Segoe UI, sans-serif",
};

const frameStyle = {
  margin: "0 auto",
  maxWidth: "1120px",
  display: "grid",
  gap: "24px",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "16px",
  padding: "16px 20px",
  border: "1px solid #334155",
  borderRadius: "16px",
  backgroundColor: "#111c34",
};

const sectionBadgeStyle = {
  color: "#93c5fd",
  fontSize: "14px",
  border: "1px solid #334155",
  borderRadius: "999px",
  padding: "8px 12px",
  backgroundColor: "#0f172a",
};

const contentStyle = {
  display: "grid",
  gap: "24px",
};

export function AppLayout({ currentSection, children }: AppLayoutProps) {
  return (
    <main style={shellStyle}>
      <div style={frameStyle}>
        <header style={headerStyle}>
          <div>
            <strong>Zabbix SLA</strong>
            <div style={{ color: "#94a3b8", fontSize: "14px" }}>
              Technical dashboard for SLA monitoring
            </div>
          </div>
          <div aria-label="Current section" style={sectionBadgeStyle}>
            Current section: {currentSection}
          </div>
        </header>
        <div style={contentStyle}>{children}</div>
      </div>
    </main>
  );
}
