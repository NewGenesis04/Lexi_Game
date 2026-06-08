// tailwind.config.js
// Lexi — Neo-Brutalist Design System
// ====================================
// Extends Tailwind with all Lexi design tokens.
// All values reference CSS custom properties from lexi.css.
//
// USAGE:
//   Replace or merge this with your existing tailwind.config.js.
//   Ensure lexi.css is imported in main.css before Tailwind directives.
//
// CONVENTIONS:
//   Colors:  bg-lexi-bg, text-lexi-primary, border-lexi-border, etc.
//   Shadows: shadow-lexi-sm, shadow-lexi-md, shadow-lexi-lg
//   Radius:  rounded-lexi-xs, rounded-lexi-sm (cards/boards are rounded-none)
//   Fonts:   font-lexi-display, font-lexi-ui, font-lexi-numeric

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],

  // Theme switching is handled by [data-theme] attribute on <html>.
  // No Tailwind dark mode class needed — CSS vars handle it automatically.
  darkMode: ['selector', '[data-theme="dark"]'],

  theme: {
    extend: {

      // --------------------------------------------------------
      // COLORS
      // All semantic tokens — mode-aware via CSS vars.
      // --------------------------------------------------------
      colors: {
        lexi: {
          // Surfaces
          'bg':              'var(--color-bg)',
          'bg-elevated':     'var(--color-bg-elevated)',
          'bg-sunken':       'var(--color-bg-sunken)',

          // Text
          'text':            'var(--color-text-primary)',
          'text-secondary':  'var(--color-text-secondary)',
          'text-muted':      'var(--color-text-muted)',
          'text-on-accent':  'var(--color-text-on-accent)',
          'text-on-dark':    'var(--color-text-on-dark)',

          // Brand
          'primary':         'var(--color-primary)',
          'primary-hover':   'var(--color-primary-hover)',
          'primary-subtle':  'var(--color-primary-subtle)',

          // Secondary
          'secondary':       'var(--color-secondary)',
          'secondary-hover': 'var(--color-secondary-hover)',
          'secondary-subtle':'var(--color-secondary-subtle)',
          'text-on-secondary':'var(--color-text-on-secondary)',

          // Semantic
          'danger':          'var(--color-danger)',
          'danger-hover':    'var(--color-danger-hover)',
          'danger-subtle':   'var(--color-danger-subtle)',
          'success':         'var(--color-success)',
          'success-subtle':  'var(--color-success-subtle)',
          'warning':         'var(--color-warning)',
          'warning-subtle':  'var(--color-warning-subtle)',

          // Borders
          'border':          'var(--color-border)',
          'border-subtle':   'var(--color-border-subtle)',
          'border-muted':    'var(--color-border-muted)',

          // Tiles (rack)
          'tile':            'var(--color-tile-bg)',
          'tile-border':     'var(--color-tile-border)',
          'tile-text':       'var(--color-tile-text)',
          'tile-points':     'var(--color-tile-points)',
          'tile-selected':        'var(--color-tile-selected-bg)',
          'tile-selected-text':   'var(--color-tile-selected-text)',
          'tile-selected-border': 'var(--color-tile-selected-border)',
          'tile-rack':            'var(--color-tile-rack-bg)',

          // Player panel
          'panel':           'var(--color-panel-bg)',
          'panel-border':    'var(--color-panel-border)',
          'panel-accent':    'var(--color-panel-active-accent)',
          'score':           'var(--color-panel-score)',
          'clock-urgent':    'var(--color-panel-clock-urgent)',

          // Connection dots
          'dot-active':      'var(--color-dot-active)',
          'dot-waiting':     'var(--color-dot-waiting)',
          'dot-offline':     'var(--color-dot-offline)',

          // Header
          'header':          'var(--color-header-bg)',
          'header-border':   'var(--color-header-border)',

          // Notification bar
          'notif':           'var(--color-notif-bg)',
          'notif-text':      'var(--color-notif-text)',

          // Board
          'board':           'var(--color-board-bg)',
          'board-border':    'var(--color-board-border)',
          'cell':            'var(--color-cell-empty-bg)',
          'cell-border':     'var(--color-cell-empty-border)',

          // Board squares
          'sq-dl':           'var(--color-sq-dl-bg)',
          'sq-dl-label':     'var(--color-sq-dl-label)',
          'sq-dl-border':    'var(--color-sq-dl-border)',

          'sq-tl':           'var(--color-sq-tl-bg)',
          'sq-tl-label':     'var(--color-sq-tl-label)',
          'sq-tl-border':    'var(--color-sq-tl-border)',

          'sq-dw':           'var(--color-sq-dw-bg)',
          'sq-dw-label':     'var(--color-sq-dw-label)',
          'sq-dw-border':    'var(--color-sq-dw-border)',

          'sq-tw':           'var(--color-sq-tw-bg)',
          'sq-tw-label':     'var(--color-sq-tw-label)',
          'sq-tw-border':    'var(--color-sq-tw-border)',

          'sq-star':         'var(--color-sq-star-bg)',
          'sq-star-label':   'var(--color-sq-star-label)',
          'sq-star-border':  'var(--color-sq-star-border)',

          // Placed tile (board)
          'placed':          'var(--color-tile-placed-bg)',
          'placed-text':     'var(--color-tile-placed-text)',
          'placed-points':   'var(--color-tile-placed-points)',
          'placed-border':   'var(--color-tile-placed-border)',

          // Overlays
          'overlay':         'var(--color-overlay-bg)',
          'overlay-card':    'var(--color-overlay-card-bg)',
          'overlay-border':  'var(--color-overlay-card-border)',
        },
      },

      // --------------------------------------------------------
      // BOX SHADOWS (neo-brutalist: no blur, pure offset)
      // --------------------------------------------------------
      boxShadow: {
        'lexi-sm':      'var(--shadow-sm)',
        'lexi-md':      'var(--shadow-md)',
        'lexi-lg':      'var(--shadow-lg)',
        'lexi-pressed': 'var(--shadow-pressed)',
        'lexi-none':    'none',

        // Tile-specific
        'lexi-tile':         'var(--shadow-sm)',
        'lexi-tile-hover':   'var(--tile-hover-shadow)',
        'lexi-tile-selected':'var(--tile-selected-shadow)',
      },

      // --------------------------------------------------------
      // BORDER RADIUS
      // --------------------------------------------------------
      borderRadius: {
        'lexi-none': '0px',
        'lexi-xs':   '2px',
        'lexi-sm':   '4px',
      },

      // --------------------------------------------------------
      // BORDER WIDTH
      // --------------------------------------------------------
      borderWidth: {
        'lexi':       '2px',
        'lexi-heavy': '3px',
        'lexi-light': '1px',
      },

      // --------------------------------------------------------
      // FONT FAMILIES
      // --------------------------------------------------------
      fontFamily: {
        'lexi-display': ['EB Garamond', 'Georgia', 'serif'],
        'lexi-ui':      ['Space Mono', 'Courier New', 'monospace'],
        'lexi-numeric': ['Space Mono', 'monospace'],
      },

      // --------------------------------------------------------
      // FONT SIZES (with default line-heights)
      // --------------------------------------------------------
      fontSize: {
        'lexi-xs':   ['10px', { lineHeight: '1.4', letterSpacing: '0.08em' }],
        'lexi-sm':   ['12px', { lineHeight: '1.4', letterSpacing: '0.08em' }],
        'lexi-base': ['14px', { lineHeight: '1.5', letterSpacing: '0.08em' }],
        'lexi-md':   ['16px', { lineHeight: '1.5' }],
        'lexi-lg':   ['18px', { lineHeight: '1.4' }],
        'lexi-xl':   ['24px', { lineHeight: '1.3' }],
        'lexi-2xl':  ['32px', { lineHeight: '1.2' }],
        'lexi-3xl':  ['48px', { lineHeight: '1.1' }],
      },

      // --------------------------------------------------------
      // LETTER SPACING
      // --------------------------------------------------------
      letterSpacing: {
        'lexi-ui':    '0.08em',
        'lexi-wide':  '0.12em',
        'lexi-tight': '-0.02em',
      },

      // --------------------------------------------------------
      // TRANSITIONS
      // --------------------------------------------------------
      transitionDuration: {
        'lexi-fast':   '100ms',
        'lexi-base':   '150ms',
        'lexi-spring': '200ms',
      },

      transitionTimingFunction: {
        'lexi-spring': 'cubic-bezier(0.34, 1.20, 0.64, 1)',
      },

      // --------------------------------------------------------
      // SPACING (a few Lexi-specific sizes)
      // --------------------------------------------------------
      spacing: {
        'lexi-tile': '44px',   // Rack tile size
        'lexi-cell': '36px',   // Board cell size
        'lexi-panel': '176px', // Player panel width
      },

      // --------------------------------------------------------
      // ANIMATIONS
      // --------------------------------------------------------
      keyframes: {
        'lexi-slide-up': {
          from: { transform: 'translateY(100%)', opacity: '0' },
          to:   { transform: 'translateY(0)',    opacity: '1' },
        },
        'lexi-fade-in': {
          from: { opacity: '0', transform: 'scale(0.97)' },
          to:   { opacity: '1', transform: 'scale(1)' },
        },
        'lexi-pulse-dot': {
          '0%, 100%': { opacity: '1' },
          '50%':       { opacity: '0.35' },
        },
        'lexi-tile-place': {
          '0%':   { transform: 'scale(1.15) translateY(-4px)' },
          '60%':  { transform: 'scale(0.97) translateY(1px)' },
          '100%': { transform: 'scale(1) translateY(0)' },
        },
      },

      animation: {
        'lexi-slide-up':   'lexi-slide-up 250ms ease forwards',
        'lexi-fade-in':    'lexi-fade-in 350ms ease forwards',
        'lexi-pulse-dot':  'lexi-pulse-dot 2s ease-in-out infinite',
        'lexi-tile-place': 'lexi-tile-place 180ms cubic-bezier(0.34, 1.20, 0.64, 1) forwards',
      },
    },
  },

  plugins: [],
}
