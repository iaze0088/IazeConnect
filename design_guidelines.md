# IAZE WhatsApp Management System - Premium Design Guidelines

## Design Approach
**Premium Dashboard Aesthetic**: Material Design 3 foundation with sophisticated dark theme customization
- Inspired by Vercel, Linear, and Stripe dashboards
- Focus: Elegant information density with visual refinement
- Dark palette with strategic accent colors and glassmorphism effects

## Color System

**Foundation**:
- Background Primary: `#0f172a` (slate-950)
- Background Secondary: `#1e293b` (slate-800)
- Surface/Cards: `#1e293b` with subtle gradients

**Accents** (Vibrant & High Contrast):
- Electric Blue: `#60a5fa` (HSL 217 88% 64%) - primary actions, links, active states
- Success Green: `#34d399` (HSL 160 90% 46%) - connected status, positive metrics
- Warning Amber: `#fbbf24` (HSL 38 96% 58%) - alerts, connecting states
- Error Red: `#f87171` (HSL 0 90% 62%) - disconnected, errors

**Design Note**: Colors increased in saturation and lightness for better visibility and user comprehension. Previous palette was too muted.

**Text Hierarchy**:
- Primary: `#f1f5f9` (slate-100)
- Secondary: `#94a3b8` (slate-400)
- Tertiary: `#64748b` (slate-500)

**Glassmorphism**:
- Cards: `backdrop-blur-xl bg-slate-800/40` with `border border-slate-700/50`
- Overlays: `bg-slate-900/80 backdrop-blur-md`

## Typography System

**Font Families**: Inter (UI), JetBrains Mono (code/logs)

**Scale**:
- H1: `text-3xl font-semibold` (30px) - Page titles with gradient text effect
- H2: `text-2xl font-semibold` (24px) - Section headers
- H3: `text-lg font-medium` (18px) - Card titles
- Body Large: `text-base` (16px) - Primary content
- Body: `text-sm` (14px) - Secondary content
- Caption: `text-xs` (12px) - Timestamps, metadata
- Mono: `font-mono text-sm` - API keys, logs, code snippets

**Special Effects**:
- Page titles: Gradient text `from-blue-400 to-cyan-400`
- Interactive text: Smooth color transitions on hover

## Layout System

**Spacing**: Tailwind units of 3, 4, 6, 8, 12, 16, 20, 24 for generous breathing room
- Section padding: `py-12` to `py-20`
- Card internal: `p-8`
- Component gaps: `gap-6` (related), `gap-10` (sections)

**Grid System**:
- Dashboard containers: `max-w-7xl mx-auto px-6`
- Metric cards: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6`
- Connection cards: `grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6`

## Core Layout Structure

### Navigation Sidebar
- Width: `w-72` (288px) - More spacious than standard
- Background: `bg-slate-900/50 backdrop-blur-xl border-r border-slate-800`
- Nav items: `px-4 py-3 rounded-lg` with smooth hover states
- Active: `bg-blue-500/10 text-blue-400 border-l-2 border-blue-500`
- Icons: 20px with `text-slate-400` default, `text-blue-400` active

### Top App Bar
- Height: `h-16`
- Background: `bg-slate-900/80 backdrop-blur-lg border-b border-slate-800`
- Search bar: Glassmorphic with `bg-slate-800/50 backdrop-blur`
- Profile menu: Avatar with online indicator dot

### Main Content
- Left margin: `ml-72`
- Background: Subtle gradient `from-slate-950 to-slate-900`
- Content padding: `p-8`

## Component Library

### Real-Time Metric Cards
- Layout: 4-column grid on desktop
- Card style: Glassmorphic `backdrop-blur-xl bg-gradient-to-br from-slate-800/60 to-slate-800/30`
- Border: `border border-slate-700/50 rounded-2xl`
- Padding: `p-6`
- Content: Icon (32px gradient), large number (text-3xl font-bold), label, trend indicator (↑↓ with percentage)
- Hover: Subtle lift `hover:translate-y-[-2px] transition-transform duration-300`

### WhatsApp QR Connection Module
- Centered card: `max-w-2xl mx-auto`
- Premium elevation: `shadow-2xl shadow-blue-500/10`
- Header: Large "CONECTAR NÚMERO" button with gradient `bg-gradient-to-r from-blue-500 to-cyan-500`
- QR Display: `min-h-80` centered with animated border pulse when connecting
- Status indicator: Colored dot + text with smooth status transitions
- Connection info: Glassmorphic panel below QR with phone, duration, device info

### Modern Chart Components
- Line/Area charts: Gradient fills `from-blue-500/20 to-transparent`
- Grid lines: `stroke-slate-800`
- Tooltips: Dark glassmorphic cards
- Legends: Horizontal with colored dots
- Real-time update: Smooth animation for data points

### Connection Status Grid
- Cards: `rounded-xl backdrop-blur-xl bg-slate-800/40`
- Avatar: 48px circular with online status ring
- Status badges: Glowing effect with matching accent color
- Quick actions: Icon buttons with `hover:bg-slate-700/50`
- Connection strength indicator: Signal bars with color coding

### Session Table (Premium)
- Header: Sticky with `backdrop-blur-lg bg-slate-900/80`
- Rows: `hover:bg-slate-800/30 transition-colors`
- Alternating subtle background for readability
- Column headers: Sortable with animated chevrons
- Status cells: Badge with glow effect matching status color
- Actions: Dropdown menu with glassmorphic overlay

### Logs Terminal
- Background: `bg-slate-950 rounded-xl border border-slate-800`
- Font: JetBrains Mono throughout
- Padding: `p-6`
- Line height: Generous `leading-relaxed`
- Syntax highlighting: Info (blue), Warning (amber), Error (red), Success (green)
- Timestamp: `text-slate-500`
- Auto-scroll indicator: Floating button with pulse animation
- Copy button: Top-right with smooth icon transition on click

### Form Components
- Inputs: `bg-slate-800/50 border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20`
- Height: `h-12 rounded-lg px-4`
- Labels: `text-sm text-slate-300 mb-2`
- Helper text: `text-xs text-slate-500 mt-1`
- API key fields: Monospace with reveal toggle, copy button on hover

## Animation System

**Purposeful & Smooth**:
- Page transitions: Fade-in `duration-400 ease-out`
- Card hover: `transform scale-[1.01] duration-300`
- Status changes: Color transition `transition-all duration-500`
- QR code appearance: Scale + fade `duration-600 ease-out`
- Real-time data: Smooth chart animations with spring physics
- Button interactions: Scale down on click `active:scale-95`
- Loading states: Skeleton pulse with gradient shimmer

**Micro-interactions**:
- Copy button: Checkmark animation on success
- Connection toggle: Smooth slide with color morph
- Notification badges: Bounce entrance
- Metric changes: Number count-up animation

## Special Visual Effects

**Gradients**:
- Card backgrounds: Subtle `from-slate-800/60 to-slate-800/30`
- Button primaries: `from-blue-500 to-cyan-500`
- Text accents: `from-blue-400 to-cyan-400`
- Glow effects on status indicators

**Shadows**:
- Cards: `shadow-xl shadow-slate-900/50`
- Elevated: `shadow-2xl shadow-blue-500/5`
- Glow: `shadow-lg shadow-blue-500/30` for active elements

**Borders**:
- Standard: `border-slate-700/50`
- Active: `border-blue-500/50`
- Glow border: Add `ring-1 ring-blue-500/20` for emphasis

## Page Layouts

### Dashboard Home
- Metric row: 4 cards (Total, Active, Errors, Response Time)
- Activity chart: Full-width area chart showing connections over time
- Recent sessions: Table with last 10 connections
- Quick actions: Floating action button group (bottom-right)

### WhatsApp Connection
- Hero QR module: Centered with generous spacing
- Instructions: Above QR with icon, step-by-step
- Connection history: Timeline view in sidebar (if desktop) or below (mobile)
- Device info panel: Shows WhatsApp version, device type

### Logs Viewer
- Full-width terminal aesthetic
- Filter toolbar: Pills for level selection with count badges
- Time range selector: Glassmorphic dropdown
- Search: Highlighted matches with scroll-to navigation
- Export: Button with format options (JSON, TXT, CSV)

## Responsive Strategy
- Mobile (<768px): Sidebar slides over, single-column metrics, collapsible sections
- Tablet (768-1024px): 2-column metrics, visible sidebar toggle
- Desktop (>1024px): Full 4-column metrics, persistent sidebar

## Accessibility
- Touch targets: `min-h-12 min-w-12`
- Focus rings: `ring-2 ring-blue-500 ring-offset-2 ring-offset-slate-900`
- Status: Icon + text + color (triple encoding)
- Keyboard nav: Visible focus with enhanced contrast
- Screen readers: ARIA labels on all interactive elements

## Images
No hero images required. Functional imagery only:
- QR Code: Dynamic API-generated, centered in glassmorphic card
- Avatars: 48px circular with gradient borders for online users
- Empty states: Minimalist SVG icons with soft glow effects