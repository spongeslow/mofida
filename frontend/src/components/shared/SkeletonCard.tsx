/**
 * SkeletonCard — shimmer placeholder that matches the shape of the content it
 * stands in for (H5.5). Use `rows` to control how many lines.
 */
import { card } from "../../theme";

export function SkeletonLine({ width = "100%", height = 12 }: { width?: string | number; height?: number }) {
  return <div className="mf-skeleton" style={{ width, height, marginBottom: 8 }} />;
}

export function SkeletonCard({ rows = 3, title = true }: { rows?: number; title?: boolean }) {
  return (
    <div style={card} aria-busy="true">
      {title && <SkeletonLine width="40%" height={16} />}
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonLine key={i} width={`${90 - i * 8}%`} />
      ))}
    </div>
  );
}
