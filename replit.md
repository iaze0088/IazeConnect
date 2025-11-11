# IAZE - Sistema Multi-Tenant de Atendimento

## Overview

IAZE is a professional multi-tenant WhatsApp customer service management system integrated with WPP Connect. It supports multiple resellers with data isolation, four user types (Admin, Reseller, Agent, Client), and three communication channels (WA SUPPORT, WHATSAPP, WA SITE). The system aims to streamline customer interactions via WhatsApp, offering a robust and scalable solution for businesses.

## User Preferences

I prefer simple language and clear explanations. I want iterative development with frequent updates and feedback. Ask before making major architectural changes or introducing new technologies. I value detailed explanations for complex implementations.

## System Architecture

The system follows a client-server architecture with a React-based frontend and a Node.js/Express backend.

### Frontend (React + TypeScript)
- **Framework**: React 19 with Wouter for routing.
- **UI/UX**: Shadcn/ui + Tailwind CSS with premium dark glassmorphic theme.
- **State Management**: TanStack Query v5.
- **Real-time**: WebSocket for QR Code and status updates.
- **Design System (Premium)**: 
  - Dark palette: Slate backgrounds (#0f172a, #1e293b), Electric Blue primary (#3b82f6), Success Green (#10b981), Warning Amber (#f59e0b)
  - Glassmorphism: backdrop-blur-xl, gradient overlays, animated borders
  - Typography: Inter (UI), JetBrains Mono (code/logs)
  - Custom scrollbar with primary accent
  - Inspired by Vercel/Linear/Stripe dashboards
  - Split-pane layouts for optimal information density
  - Generous spacing (space-y-10, gap-6) for breathing room

### Backend (Node.js + Express)
- **Runtime**: Node.js 20.
- **API**: Express.js with RESTful endpoints.
- **WhatsApp Integration**: `@wppconnect-team/wppconnect` for WhatsApp management, integrated with an external WPP Connect server.
- **Storage**: Custom ExtendedMemStorage (in-memory) for 7 IAZE entities (Resellers, Users, Clients, Agents, Departments, Tickets, Messages), with PostgreSQL support prepared for production.
- **Authentication**: JWT signed tokens (7-day expiration) using `jsonwebtoken`, `bcrypt` for password/PIN hashing, and role-based authorization middleware.
- **Real-time**: WebSocket Server (path: `/ws`) for broadcasting real-time updates (e.g., QR codes, connection status).

### Core Features
- **Data Import**: Supports importing 12,941 records from MongoDB backups (Resellers, Users, Clients, Agents, Departments, Tickets, Messages).
- **Authentication System**: Secure JWT-based authentication for Admin, Reseller, Agent, and Client roles, including client registration with WhatsApp and PIN.
- **Multi-tenancy**: Data isolation by `resellerId` for secure multi-tenant operations.
- **WPP Connect Integration**: Manages WhatsApp sessions, generates/retrieves QR codes, checks connection status, and sends messages via an external WPP Connect API. Includes robust token management and retry logic.
- **Premium Dashboard**: 4 glassmorphic metric cards with gradients, trend indicators, real-time connection status with glow rings for active sessions.
- **Split-Pane WhatsApp Page**: Left column (session inventory with quick actions), right column (hero workspace with onboarding guide).
- **Premium QR Code Modal**: 
  - Glassmorphic backdrop (blur-40px)
  - Animated pulsing border with gradient glow
  - SVG countdown ring (color-coded: green >30s, yellow >15s, red <15s)
  - Success animation (glow + zoom-in checkmark + auto-close 3s)
  - Live "Aguardando scan..." status indicator
  - Contextual instructions ("Como conectar" card + FAQ link)
  - Countdown auto-resets to 45s on every modal open
- **Connection Management**: Create, start, delete, and monitor WhatsApp sessions with real-time status updates.
- **Logging**: System logs for monitoring events.

### Coding Standards
- **TypeScript**: Strict mode, explicit types.
- **React**: Functional components, hooks.
- **API**: REST with Zod validation.
- **Styling**: Tailwind CSS classes.
- **Testing**: `data-testid` for interactive elements.

## External Dependencies

- **WPP Connect API**: External WPP Connect server at `http://wppconnect.suporte.help:21465` (HTTP with explicit port) for WhatsApp communication.
- **PostgreSQL**: Planned for production database storage (currently uses in-memory `ExtendedMemStorage` for development).
- **`@wppconnect-team/wppconnect`**: Node.js library for WhatsApp Web interactions.
- **`axios`**: HTTP client for API requests to the external WPP Connect server.
- **`jsonwebtoken`**: For JWT token generation and verification.
- **`bcrypt`**: For hashing passwords and PINs.
- **`ws`**: WebSocket library for real-time communication.
- **`react`**, **`wouter`**, **`shadcn/ui`**, **`tailwindcss`**, **`tanstack/react-query`**: Frontend libraries and frameworks.