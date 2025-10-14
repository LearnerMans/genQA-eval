import { useState, useEffect } from 'react';
import { themes as themeDefinitions } from '../theme/themes';

const themeList = [
  { id: 'modernBlue', name: themeDefinitions.modernBlue.name },
  { id: 'dark', name: themeDefinitions.dark.name }
];

export default function ThemeSwitcher() {
  const [selectedTheme, setSelectedTheme] = useState(() => {
    return localStorage.getItem('selected-theme') || 'modernBlue';
  });
  const [isOpen, setIsOpen] = useState(false);

  const applyTheme = (themeId) => {
    const theme = themeDefinitions[themeId];
    if (!theme) return;

    // Apply all CSS variables to the root element
    const root = document.documentElement;
    Object.entries(theme.colors).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });
  };

  const switchTheme = (themeId) => {
    setSelectedTheme(themeId);
    localStorage.setItem('selected-theme', themeId);
    applyTheme(themeId);
    setIsOpen(false);
  };

  // Load saved theme (or default to Modern Blue) on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('selected-theme');
    const themeToApply = savedTheme || 'modernBlue';
    setSelectedTheme(themeToApply);
    applyTheme(themeToApply);
  }, []);

  return (
    <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999 }}>
      <div style={{ position: 'relative' }}>
        {/* Theme Dropdown */}
        {isOpen && (
          <div style={{
            position: 'absolute',
            bottom: '60px',
            right: '0',
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            minWidth: '220px',
            overflow: 'hidden'
          }}>
            <div style={{
              padding: '12px 16px',
              borderBottom: '1px solid var(--color-border)',
              fontWeight: '600',
              fontSize: '14px',
              color: 'var(--color-text-primary)'
            }}>
              Choose Theme
            </div>
            {themeList.map(theme => (
              <button
                key={theme.id}
                onClick={() => switchTheme(theme.id)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  textAlign: 'left',
                  border: 'none',
                  backgroundColor: selectedTheme === theme.id ? 'var(--color-primary-light)' : 'transparent',
                  color: selectedTheme === theme.id ? 'var(--color-primary)' : 'var(--color-text-primary)',
                  cursor: 'pointer',
                  fontSize: '14px',
                  transition: 'background-color 0.2s',
                  fontWeight: selectedTheme === theme.id ? '600' : '400'
                }}
                onMouseEnter={(e) => {
                  if (selectedTheme !== theme.id) {
                    e.target.style.backgroundColor = 'var(--color-surface-hover)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedTheme !== theme.id) {
                    e.target.style.backgroundColor = 'transparent';
                  }
                }}
              >
                {theme.name}
                {selectedTheme === theme.id && (
                  <span style={{ marginLeft: '8px', color: 'var(--color-primary)' }}>✓</span>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Toggle Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          style={{
            width: '50px',
            height: '50px',
            borderRadius: '50%',
            border: '2px solid var(--color-border)',
            backgroundColor: 'var(--color-surface)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
            transition: 'all 0.2s',
            color: 'var(--color-text-primary)'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'scale(1.05)';
            e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'scale(1)';
            e.target.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
          }}
          title="Switch Theme"
        >
          🎨
        </button>
      </div>
    </div>
  );
}
