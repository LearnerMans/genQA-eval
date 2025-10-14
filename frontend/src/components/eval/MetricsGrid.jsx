export default function MetricsGrid({ children, cols = 4 }) {
  const gridClass = cols === 3 ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' : cols === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4';
  return (
    <div className={`grid ${gridClass} gap-3`}>
      {children}
    </div>
  );
}

