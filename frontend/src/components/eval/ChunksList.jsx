import ChunkItem from './ChunkItem.jsx';

export default function ChunksList({ items }) {
  if (!items || items.length === 0) {
    return (
      <div className="font-body text-sm text-text/60">No chunks were linked for this evaluation.</div>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {items.map((c, i) => (
        <ChunkItem
          key={`${c.chunk_id}-${i}`}
          indexLabel={`Chunk ${typeof c.chunk_index === 'number' ? c.chunk_index : i + 1}`}
          content={c.content}
          sourceType={c.source_type}
          source={c.source}
        />
      ))}
    </div>
  );
}

