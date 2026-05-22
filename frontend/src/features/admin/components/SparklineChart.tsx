export default function SparklineChart({ data }: { data: { date: string; count: number }[] }) {
  if (!data.length) return null;

  const max = Math.max(...data.map((d) => d.count), 1);
  const width = 120;
  const height = 32;
  const points = data
    .map((d, i) => `${(i / (data.length - 1)) * width},${height - (d.count / max) * height}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-8">
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="text-blue-600"
        points={points}
      />
    </svg>
  );
}
