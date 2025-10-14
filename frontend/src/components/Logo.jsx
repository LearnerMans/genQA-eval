import logoImage from '../assets/logo.png';

export default function Logo({ size = 'md', showText = true }) {
  const sizes = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
    xl: 'h-24 w-24'
  };

  const textSizes = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl',
    xl: 'text-3xl'
  };

  const handleClick = () => {
    window.location.hash = '#';
  };

  return (
    <div
      onClick={handleClick}
      className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
      aria-label="Go to Projects"
    >
      <img
        src={logoImage}
        alt="ChunkLab Logo"
        className={`${sizes[size]} object-contain`}
      />
      {showText && (
        <span className={`font-heading font-bold ${textSizes[size]} text-text`}>
          ChunkLab
        </span>
      )}
    </div>
  );
}
