"use client";

import React from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { ChartConfig } from "@/lib/types";

interface ChartRendererProps {
  config: ChartConfig;
}

const formatValue = (value: unknown): string => {
  if (typeof value === "number") {
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
    return value.toLocaleString();
  }
  return String(value);
};

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-xl px-4 py-3 shadow-2xl">
      <p className="text-gray-400 text-xs mb-1.5 font-medium">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-sm font-semibold" style={{ color: entry.color }}>
          {entry.name}: {formatValue(entry.value)}
        </p>
      ))}
    </div>
  );
};

export default function ChartRenderer({ config }: ChartRendererProps) {
  const { chart_type, data, x_key, y_key, colors, x_label, y_label } = config;

  if (!data?.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>No data to display</p>
      </div>
    );
  }

  const commonProps = {
    data,
    margin: { top: 10, right: 30, left: 10, bottom: 20 },
  };

  const axisStyle = {
    fontSize: 11,
    fill: "#9ca3af",
    fontFamily: "Inter, system-ui, sans-serif",
  };

  switch (chart_type) {
    case "bar":
      return (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis
              dataKey={x_key}
              tick={axisStyle}
              axisLine={{ stroke: "#4b5563" }}
              tickLine={false}
              label={x_label ? { value: x_label, position: "bottom", style: { ...axisStyle, fontSize: 12 } } : undefined}
            />
            <YAxis
              tick={axisStyle}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => formatValue(v)}
              label={y_label ? { value: y_label, angle: -90, position: "insideLeft", style: { ...axisStyle, fontSize: 12 } } : undefined}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(99, 102, 241, 0.1)" }} />
            <Bar
              dataKey={y_key}
              radius={[6, 6, 0, 0]}
              maxBarSize={60}
            >
              {data.map((_, index) => (
                <Cell key={index} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      );

    case "line":
      return (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart {...commonProps}>
            <defs>
              <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors[0]} stopOpacity={0.3} />
                <stop offset="95%" stopColor={colors[0]} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis dataKey={x_key} tick={axisStyle} axisLine={{ stroke: "#4b5563" }} tickLine={false} />
            <YAxis tick={axisStyle} axisLine={false} tickLine={false} tickFormatter={(v) => formatValue(v)} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey={y_key}
              stroke={colors[0]}
              strokeWidth={3}
              dot={{ r: 4, fill: colors[0], strokeWidth: 2, stroke: "#1f2937" }}
              activeDot={{ r: 6, fill: colors[0], stroke: "#fff", strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      );

    case "area":
      return (
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart {...commonProps}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors[0]} stopOpacity={0.4} />
                <stop offset="95%" stopColor={colors[0]} stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis dataKey={x_key} tick={axisStyle} axisLine={{ stroke: "#4b5563" }} tickLine={false} />
            <YAxis tick={axisStyle} axisLine={false} tickLine={false} tickFormatter={(v) => formatValue(v)} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey={y_key}
              stroke={colors[0]}
              strokeWidth={2.5}
              fill="url(#areaGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      );

    case "pie":
      return (
        <ResponsiveContainer width="100%" height={320}>
          <PieChart>
            <Pie
              data={data}
              dataKey={y_key}
              nameKey={x_key}
              cx="50%"
              cy="50%"
              outerRadius={120}
              innerRadius={60}
              strokeWidth={2}
              stroke="#1f2937"
              label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`}
              labelLine={{ stroke: "#6b7280" }}
            >
              {data.map((_, index) => (
                <Cell key={index} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 12, color: "#9ca3af" }}
            />
          </PieChart>
        </ResponsiveContainer>
      );

    case "table":
      return (
        <div className="overflow-x-auto max-h-80">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700/50">
                {Object.keys(data[0] || {}).map((key) => (
                  <th
                    key={key}
                    className="text-left py-3 px-4 text-gray-400 font-medium text-xs uppercase tracking-wider"
                  >
                    {key.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 50).map((row, i) => (
                <tr
                  key={i}
                  className="border-b border-gray-800/30 hover:bg-gray-800/30 transition-colors"
                >
                  {Object.values(row).map((val, j) => (
                    <td key={j} className="py-2.5 px-4 text-gray-300">
                      {typeof val === "number" ? val.toLocaleString() : String(val)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

    default:
      return <p className="text-gray-500">Unsupported chart type: {chart_type}</p>;
  }
}
