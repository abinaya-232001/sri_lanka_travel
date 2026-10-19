import { useState, useRef, useEffect, useMemo } from "react";
import { useSiteI18n } from "@shared/i18n/react";

export default function DistrictSelect({ districts, value, onChange, placeholder }) {
  const { t } = useSiteI18n();
  const resolvedPlaceholder = placeholder || t("ldAllDistrictsLower");
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);
  const wrapRef = useRef(null);

  const options = useMemo(() => ["All", ...districts], [districts]);

  const filtered = useMemo(() => {
    if (!query.trim()) return options;
    const q = query.toLowerCase();
    return options.filter((d) => d.toLowerCase().includes(q));
  }, [query, options]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function selectOption(opt) {
    onChange(opt);
    setQuery("");
    setOpen(false);
  }

  function handleKeyDown(e) {
    if (!open && (e.key === "ArrowDown" || e.key === "Enter")) {
      setOpen(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[highlight]) selectOption(filtered[highlight]);
    } else if (e.key === "Escape") {
      setOpen(false);
      setQuery("");
    }
  }

  return (
    <div ref={wrapRef} style={{ position: "relative", minWidth: 180 }}>
      <input
        type="text"
        value={open ? query : value === "All" ? "" : value}
        placeholder={value === "All" ? resolvedPlaceholder : value}
        onFocus={() => {
          setOpen(true);
          setHighlight(0);
        }}
        onChange={(e) => {
          setQuery(e.target.value);
          setHighlight(0);
          if (!open) setOpen(true);
        }}
        onKeyDown={handleKeyDown}
        style={{
          width: "100%",
          padding: "10px 12px",
          borderRadius: 8,
          border: "1px solid #d0d5dd",
          fontSize: 14,
          fontFamily: "inherit",
          outline: "none",
          background: "#fff",
        }}
      />
      {open && (
        <ul
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            maxHeight: 240,
            overflowY: "auto",
            background: "#fff",
            border: "1px solid #d0d5dd",
            borderRadius: 8,
            boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
            listStyle: "none",
            margin: 0,
            padding: 4,
            zIndex: 50,
          }}
        >
          {filtered.length === 0 && (
            <li style={{ padding: "8px 10px", color: "#888", fontSize: 13 }}>{t("ldNoMatchingDistrict")}</li>
          )}
          {filtered.map((opt, i) => (
            <li
              key={opt}
              onMouseEnter={() => setHighlight(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                selectOption(opt);
              }}
              style={{
                padding: "8px 10px",
                borderRadius: 6,
                cursor: "pointer",
                fontSize: 14,
                background: i === highlight ? "#f0f4ff" : "transparent",
                fontWeight: opt === value ? 600 : 400,
              }}
            >
              {opt === "All" ? t("ldAllDistrictsLower") : opt}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
