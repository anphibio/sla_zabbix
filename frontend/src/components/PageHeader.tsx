import React from "react";

type PageHeaderProps = {
  title: string;
  description: string;
  eyebrow?: string;
};

const wrapperStyle = {
  display: "grid",
  gap: "8px",
};

export function PageHeader({
  title,
  description,
  eyebrow,
}: PageHeaderProps) {
  return (
    <header style={wrapperStyle}>
      {eyebrow ? (
        <span style={{ color: "#38bdf8", fontSize: "12px", letterSpacing: "0.08em" }}>
          {eyebrow}
        </span>
      ) : null}
      <h1 style={{ margin: 0, fontSize: "32px" }}>{title}</h1>
      <p style={{ margin: 0, color: "#94a3b8", maxWidth: "720px" }}>{description}</p>
    </header>
  );
}
