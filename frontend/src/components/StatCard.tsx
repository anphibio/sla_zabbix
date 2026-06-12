import React from "react";

type StatCardProps = {
  label: string;
  value: string;
  hint: string;
};

const cardStyle = {
  padding: "20px",
  border: "1px solid #334155",
  borderRadius: "16px",
  backgroundColor: "#111c34",
};

export function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <article style={cardStyle}>
      <div style={{ color: "#94a3b8", fontSize: "14px" }}>{label}</div>
      <div style={{ marginTop: "8px", fontSize: "28px", fontWeight: 700 }}>{value}</div>
      <div style={{ marginTop: "8px", color: "#cbd5e1", fontSize: "14px" }}>{hint}</div>
    </article>
  );
}
