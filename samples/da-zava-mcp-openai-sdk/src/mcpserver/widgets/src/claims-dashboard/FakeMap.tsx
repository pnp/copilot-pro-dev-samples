import React, { useMemo } from "react";
import { Text, Badge } from "@fluentui/react-components";
import { LocationRegular } from "@fluentui/react-icons";
import type { ThemeColors } from "../hooks/useThemeColors";

/**
 * A beautiful SVG-based fake map that renders a realistic city-block layout
 * with a location pin, street grid, parks, and labels. Fully theme-aware.
 */
export function FakeMap({ address, colors, style }: {
  address: string;
  colors: ThemeColors;
  style?: React.CSSProperties;
}) {
  /* Deterministic pseudo-random from address for varied layouts */
  const seed = useMemo(() => {
    let h = 0;
    for (let i = 0; i < address.length; i++) h = ((h << 5) - h + address.charCodeAt(i)) | 0;
    return Math.abs(h);
  }, [address]);

  const r = (n: number) => ((seed * (n + 1) * 9301 + 49297) % 233280) / 233280;

  /* Generate city blocks */
  const blocks = useMemo(() => {
    const b: { x: number; y: number; w: number; h: number; type: string }[] = [];
    const cols = 6, rows = 5;
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const x = 30 + col * 75 + r(row * cols + col) * 10;
        const y = 25 + row * 60 + r(col * rows + row + 100) * 8;
        const w = 55 + r(row + col * 2) * 12;
        const h = 40 + r(col + row * 3) * 10;
        const v = r(row * cols + col + 50);
        const type = v < 0.12 ? "park" : v < 0.2 ? "water" : "building";
        b.push({ x, y, w, h, type });
      }
    }
    return b;
  }, [seed]);

  /* Pin position — center area with slight offset */
  const pinX = 250 + r(42) * 40 - 20;
  const pinY = 140 + r(77) * 30 - 15;

  /* Street names */
  const streets = ["Main St", "Oak Ave", "Park Blvd", "Elm Dr", "Cedar Ln"];
  const selectedStreet = streets[seed % streets.length];

  return (
    <div style={{
      borderRadius: "12px",
      overflow: "hidden",
      border: `1px solid ${colors.border}`,
      position: "relative",
      ...style,
    }}>
      <svg viewBox="0 0 520 320" width="100%" height="100%" style={{ display: "block" }}>
        {/* Background — land */}
        <rect x="0" y="0" width="520" height="320" fill={colors.mapLand} />

        {/* Water feature */}
        <path
          d={`M 0 ${260 + r(1) * 30} Q 130 ${240 + r(2) * 40} 260 ${270 + r(3) * 30} Q 390 ${250 + r(4) * 40} 520 ${265 + r(5) * 25}`}
          stroke="none"
          fill={colors.mapWater}
          opacity="0.5"
        />
        <path
          d={`M 0 ${275 + r(1) * 30} Q 130 ${255 + r(2) * 40} 260 ${285 + r(3) * 30} Q 390 ${265 + r(4) * 40} 520 ${280 + r(5) * 25} L 520 320 L 0 320 Z`}
          fill={colors.mapWater}
          opacity="0.3"
        />

        {/* Horizontal streets */}
        {[60, 125, 190, 255].map((y, i) => (
          <g key={`h${i}`}>
            <rect x="0" y={y - 5} width="520" height={i === 1 ? 12 : 8} rx="1" fill={colors.mapRoad} opacity="0.7" />
            <line x1="0" y1={y} x2="520" y2={y} stroke={colors.border} strokeWidth="0.5" strokeDasharray="4,6" opacity="0.4" />
          </g>
        ))}

        {/* Vertical streets */}
        {[90, 170, 260, 350, 440].map((x, i) => (
          <g key={`v${i}`}>
            <rect x={x - 4} y="0" width={i === 2 ? 12 : 8} height="320" rx="1" fill={colors.mapRoad} opacity="0.7" />
            <line x1={x} y1="0" x2={x} y2="320" stroke={colors.border} strokeWidth="0.5" strokeDasharray="4,6" opacity="0.4" />
          </g>
        ))}

        {/* City blocks */}
        {blocks.map((b, i) => {
          if (b.type === "park") {
            return (
              <g key={i}>
                <rect x={b.x} y={b.y} width={b.w} height={b.h} rx="4" fill={colors.mapPark} opacity="0.6" />
                {/* Tree dots */}
                {[0.2, 0.5, 0.8].map((fx, ti) =>
                  [0.3, 0.7].map((fy, tj) => (
                    <circle key={`${ti}-${tj}`} cx={b.x + b.w * fx} cy={b.y + b.h * fy} r={3 + r(i + ti) * 2} fill={colors.mapPark} opacity="0.8" />
                  ))
                )}
              </g>
            );
          }
          if (b.type === "water") {
            return <rect key={i} x={b.x} y={b.y} width={b.w} height={b.h} rx="6" fill={colors.mapWater} opacity="0.6" />;
          }
          /* Building */
          return (
            <g key={i}>
              <rect
                x={b.x + 3} y={b.y + 3} width={b.w - 6} height={b.h - 6}
                rx="2" fill={colors.mapBuilding} opacity={0.4 + r(i) * 0.35}
              />
              {/* Building windows */}
              {r(i + 200) > 0.4 && (
                <>
                  {[0.25, 0.5, 0.75].map((fx, wi) =>
                    [0.3, 0.6].map((fy, wj) => (
                      <rect
                        key={`${wi}-${wj}`}
                        x={b.x + 3 + (b.w - 6) * fx - 1.5}
                        y={b.y + 3 + (b.h - 6) * fy - 1}
                        width="3" height="2" rx="0.5"
                        fill={colors.primary} opacity="0.15"
                      />
                    ))
                  )}
                </>
              )}
            </g>
          );
        })}

        {/* Street labels */}
        <text x="135" y="122" fontSize="7" fill={colors.mapLabel} opacity="0.6" fontFamily="system-ui" fontWeight="500" letterSpacing="2">
          {selectedStreet.toUpperCase()}
        </text>
        <text x="264" y="55" fontSize="6" fill={colors.mapLabel} opacity="0.5" fontFamily="system-ui" fontWeight="500" transform="rotate(90, 264, 55)" letterSpacing="1.5">
          BROADWAY
        </text>

        {/* Location pin — drop shadow */}
        <ellipse cx={pinX} cy={pinY + 22} rx="8" ry="3" fill="rgba(0,0,0,0.2)" />

        {/* Pin body */}
        <path
          d={`M ${pinX} ${pinY + 20} C ${pinX - 3} ${pinY + 12} ${pinX - 12} ${pinY + 2} ${pinX - 12} ${pinY - 6}
              A 12 12 0 1 1 ${pinX + 12} ${pinY - 6}
              C ${pinX + 12} ${pinY + 2} ${pinX + 3} ${pinY + 12} ${pinX} ${pinY + 20} Z`}
          fill={colors.mapPin}
          stroke="#fff"
          strokeWidth="1.5"
        />
        <circle cx={pinX} cy={pinY - 6} r="5" fill="#ffffff" opacity="0.9" />
        <circle cx={pinX} cy={pinY - 6} r="3" fill={colors.mapPin} opacity="0.7" />

        {/* Ripple rings */}
        <circle cx={pinX} cy={pinY + 22} r="14" fill="none" stroke={colors.mapPin} strokeWidth="1" opacity="0.2" />
        <circle cx={pinX} cy={pinY + 22} r="22" fill="none" stroke={colors.mapPin} strokeWidth="0.7" opacity="0.1" />

        {/* Scale bar */}
        <g transform="translate(420, 300)">
          <line x1="0" y1="0" x2="60" y2="0" stroke={colors.mapLabel} strokeWidth="1" opacity="0.4" />
          <line x1="0" y1="-3" x2="0" y2="3" stroke={colors.mapLabel} strokeWidth="1" opacity="0.4" />
          <line x1="60" y1="-3" x2="60" y2="3" stroke={colors.mapLabel} strokeWidth="1" opacity="0.4" />
          <text x="30" y="-5" fontSize="6" fill={colors.mapLabel} opacity="0.4" textAnchor="middle" fontFamily="system-ui">500 ft</text>
        </g>

        {/* Compass */}
        <g transform="translate(490, 30)">
          <circle cx="0" cy="0" r="12" fill={colors.surface} opacity="0.8" stroke={colors.border} strokeWidth="0.5" />
          <text x="0" y="-3" fontSize="7" fill={colors.mapLabel} textAnchor="middle" fontFamily="system-ui" fontWeight="700" opacity="0.6">N</text>
          <polygon points="0,-10 -2,-5 2,-5" fill={colors.mapPin} opacity="0.7" />
          <polygon points="0,10 -2,5 2,5" fill={colors.mapLabel} opacity="0.3" />
        </g>
      </svg>

      {/* Address overlay badge */}
      <div style={{
        position: "absolute",
        bottom: "12px",
        left: "12px",
        display: "flex",
        alignItems: "center",
        gap: "6px",
        padding: "6px 12px",
        borderRadius: "8px",
        backgroundColor: colors.surface,
        boxShadow: colors.shadowElevated,
        maxWidth: "70%",
      }}>
        <LocationRegular style={{ color: colors.mapPin, fontSize: "14px", flexShrink: 0 }} />
        <Text size={200} weight="semibold" style={{ color: colors.text, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {address}
        </Text>
      </div>
    </div>
  );
}
