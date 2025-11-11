# IAZE WhatsApp Management System - Design Guidelines

## Design Approach
**Design System Foundation**: Material Design 3 adapted for enterprise dashboard functionality
- Rationale: Information-dense WhatsApp connection management requires clear hierarchy, consistent patterns, and robust component library
- Focus on operational efficiency while maintaining professional polish

## Typography System

**Font Family**: Inter (primary), Roboto Mono (code/logs)
- **Headers**: Inter Semi-bold
  - H1: 2rem (32px) - Page titles
  - H2: 1.5rem (24px) - Section headers  
  - H3: 1.25rem (20px) - Card/module titles
- **Body**: Inter Regular
  - Large: 1rem (16px) - Primary content
  - Base: 0.875rem (14px) - Secondary content
  - Small: 0.75rem (12px) - Captions, timestamps
- **Monospace**: Roboto Mono 0.875rem - API keys, URLs, logs

## Layout System

**Spacing Units**: Tailwind units of 2, 4, 6, 8, 12, 16 (e.g., p-4, gap-8, mb-12)
- Consistent 8px grid system
- Section padding: py-8 to py-16
- Card internal padding: p-6
- Element spacing: gap-4 between related items, gap-8 between sections

**Container Strategy**:
- Dashboard max-width: max-w-7xl mx-auto px-4
- Cards/modules: Full width within containers with rounded-lg borders

## Core Layout Structure

### Navigation Sidebar (Fixed Left)
- Width: w-64 (256px)
- Vertical nav with icon + label pattern
- Sections: Dashboard, WhatsApp, Sessões, Logs, Configurações
- Active state: Subtle indicator bar on left edge

### Main Content Area
- Left margin: ml-64 (accounts for sidebar)
- Top app bar: h-16 with breadcrumbs and user menu
- Content grid: Single column for forms/details, multi-column (grid-cols-2 lg:grid-cols-3) for card layouts

## Component Library

### WhatsApp QR Code Module (Hero Component)
**Critical Feature - Prominent Placement**
- Large card with elevation shadow
- "CONECTAR NÚMERO" button: Prominent size (px-8 py-4), rounded-lg
- QR Code display area: Centered, min-h-64, with loading skeleton state
- Connection status indicator: Icon + text (Conectado/Desconectado/Aguardando)
- Session info below QR: Phone number, connection time

### Connection Status Cards
- Grid layout: grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6
- Each card shows: Avatar/icon, connection name, status badge, action menu
- Quick actions: Reconectar, Desconectar, Ver Logs

### Session Management Table
- Striped rows for readability
- Columns: Sessão ID, Número, Status, Última Atividade, Ações
- Sortable headers
- Inline action buttons per row

### Logs Panel
- Monospace font throughout
- Toggle filters: Info, Warning, Error, Debug
- Auto-scroll option with pause button
- Timestamp prefix on each line
- Copy log button in header

### Configuration Forms
- Single column layout, max-w-2xl
- Label above input pattern
- Input groups with helper text below
- Section dividers with descriptive headers
- API configuration: Masked secret key with reveal toggle

## Component Patterns

**Buttons**:
- Primary: px-6 py-3 rounded-lg font-medium
- Secondary: px-4 py-2 rounded border
- Icon buttons: p-2 rounded-lg (for actions in tables/cards)

**Status Badges**:
- Pill shape: px-3 py-1 rounded-full text-sm
- Icons: 16px before text
- States: Conectado, Desconectado, Conectando, Erro

**Cards**:
- Border with subtle shadow
- Rounded corners: rounded-lg
- Header with title + optional actions
- Content padding: p-6
- Hover state: Subtle lift effect

**Input Fields**:
- Height: h-12
- Border: rounded-md
- Focus: Ring effect with offset
- Disabled: Reduced opacity with cursor-not-allowed

## Page-Specific Layouts

### Dashboard (Home)
- Overview cards in 3-column grid: Total Conexões, Ativas, Erros
- Recent activity list below
- Quick action buttons

### WhatsApp Connection Page
- Centered QR code module (max-w-2xl mx-auto)
- Instructions text above: "Escaneie o QR Code com seu WhatsApp"
- Connection history sidebar (if space allows, otherwise below)

### Sessions Management
- Table view with filters at top
- Bulk actions toolbar when items selected
- Add new session button (top right)

### Logs Viewer
- Full-width layout
- Filter toolbar: Time range, level, search
- Auto-refresh toggle
- Export logs button

## Animation Guidelines
**Minimal and Purposeful**:
- QR code appearance: Fade-in only (duration-300)
- Status badge changes: Smooth transition (transition-colors)
- Card hover: Subtle scale or shadow increase
- NO scroll animations, parallax, or decorative motion

## Accessibility Standards
- All interactive elements: min-h-12 (48px touch target)
- Form labels: Visible and associated
- Status communicated via icon + text (not color alone)
- Keyboard navigation: Visible focus rings
- ARIA labels on icon-only buttons

## Responsive Behavior
- Mobile (< 768px): Sidebar collapses to hamburger menu, single-column layouts
- Tablet (768-1024px): 2-column card grids, visible sidebar
- Desktop (> 1024px): Full 3-column layouts, fixed sidebar

## Images
This is a functional dashboard application - no decorative imagery required. Only functional images:
- WhatsApp QR Code: Generated dynamically via API integration
- User avatars: Small circular (w-10 h-10) with fallback initials
- Empty state illustrations: Simple SVG icons for "No connections" or "No logs"