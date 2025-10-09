export default function Pagination({ currentPage, totalPages, onPageChange }) {
  const pages = [];
  const maxVisiblePages = 5;

  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
  let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

  if (endPage - startPage + 1 < maxVisiblePages) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center items-center gap-2 mt-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-4 py-2 border border-secondary rounded-lg font-body font-normal text-text hover:bg-accent/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
      >
        Previous
      </button>

      <div className="flex gap-1">
        {startPage > 1 && (
          <>
            <button
              onClick={() => onPageChange(1)}
              className="w-10 h-10 border border-secondary rounded-lg font-body font-normal text-text hover:bg-accent/20 transition-colors cursor-pointer"
            >
              1
            </button>
            {startPage > 2 && (
              <span className="w-10 h-10 flex items-center justify-center text-text/50">
                ...
              </span>
            )}
          </>
        )}

        {pages.map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`w-10 h-10 border rounded-lg font-body font-normal transition-colors cursor-pointer ${
              currentPage === page
                ? 'bg-primary text-white border-primary'
                : 'border-secondary text-text hover:bg-accent/20'
            }`}
          >
            {page}
          </button>
        ))}

        {endPage < totalPages && (
          <>
            {endPage < totalPages - 1 && (
              <span className="w-10 h-10 flex items-center justify-center text-text/50">
                ...
              </span>
            )}
            <button
              onClick={() => onPageChange(totalPages)}
              className="w-10 h-10 border border-secondary rounded-lg font-body font-normal text-text hover:bg-accent/20 transition-colors cursor-pointer"
            >
              {totalPages}
            </button>
          </>
        )}
      </div>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 border border-secondary rounded-lg font-body font-normal text-text hover:bg-accent/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
      >
        Next
      </button>
    </div>
  );
}
