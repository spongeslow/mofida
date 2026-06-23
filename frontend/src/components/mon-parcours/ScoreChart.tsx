import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { getScoreHistory } from "../../api";
import { C, SCORE_COLORS, card } from "../../theme";
import type { ScoreSnapshot } from "../../types";

interface ChartPoint {
  time: string;
  [score: string]: string | number;
}

function buildChartData(snapshots: ScoreSnapshot[]): ChartPoint[] {
  const byTime = new Map<string, ChartPoint>();
  for (const s of snapshots) {
    const time = new Date(s.created_at).toLocaleString();
    const existing = byTime.get(time) ?? { time };
    existing[s.score_name] = Math.round(s.score * 100) / 100;
    byTime.set(time, existing);
  }
  return Array.from(byTime.values());
}

export function ScoreChart() {
  const t = useT();
  const projectId = useStore((s) => s.projectId);
  const [data, setData] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    getScoreHistory(projectId)
      .then((r) => setData(buildChartData(r.snapshots)))
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [projectId]);

  return (
    <div style={card}>
      <p style={{ color: C.muted, fontSize: 12, margin: "0 0 16px", textTransform: "uppercase", letterSpacing: 1 }}>
        {t("score_history")}
      </p>
      {loading && <p style={{ color: C.muted }}>{t("running_diagnostic")}</p>}
      {!loading && data.length === 0 && (
        <p style={{ color: C.muted }}>{t("no_history")}</p>
      )}
      {!loading && data.length > 0 && (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <XAxis dataKey="time" tick={{ fill: C.muted, fontSize: 11 }} />
            <YAxis domain={[0, 5]} tick={{ fill: C.muted, fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8 }}
              labelStyle={{ color: C.text }}
              itemStyle={{ color: C.muted }}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: C.muted }} />
            {Object.entries(SCORE_COLORS).map(([name, color]) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={color}
                strokeWidth={2}
                dot={{ r: 4, fill: color }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
