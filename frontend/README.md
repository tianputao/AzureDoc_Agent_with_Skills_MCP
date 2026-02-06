# Azure Doc Agent - Frontend

React + TypeScript + Vite frontend for Azure Doc Agent.

## 🎨 Features

- **Dark Theme** - Modern dark UI with colorful accents
- **Sidebar Navigation** - Collapsible sidebar with skills and thread management
- **Real-time Chat** - Interactive chat interface with example queries
- **Markdown Support** - Rich text rendering for responses
- **Responsive Design** - Works on all screen sizes

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend server running on port 8000

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   ├── services/         # API services
│   ├── styles/           # CSS stylesheets
│   ├── types/            # TypeScript types
│   ├── App.tsx           # Main App component
│   └── main.tsx          # Entry point
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 🎯 Example Queries

The frontend includes 5 pre-configured example queries:

1. Azure CLI for creating container apps with managed identity
2. GPT-5.2 availability in EU regions
3. Python code examples for Azure AI Foundry evaluation SDK
4. End-to-end Azure Functions guide
5. Step-by-step Python to Azure Functions deployment tutorial

## 🎨 Theme Colors

- **Background**: Dark (#1a1a1a, #2d2d2d)
- **Accent Colors**: 
  - Blue (#4a9eff)
  - Purple (#a855f7)
  - Green (#10b981)
  - Orange (#f97316)
  - Pink (#ec4899)
  - Cyan (#06b6d4)

## 📡 API Integration

The frontend connects to the FastAPI backend via:
- REST API endpoints (`/api/*`)
- WebSocket for real-time chat (`/ws/*`)

Configuration is in `vite.config.ts` proxy settings.

## 🛠️ Development

```bash
# Run dev server
npm run dev

# Type checking
npm run build

# Lint code
npm run lint
```

## 📦 Dependencies

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering

## 🚢 Deployment

The production build can be served statically or deployed to:
- Vercel
- Netlify
- Azure Static Web Apps
- Any static hosting service

```bash
npm run build
# dist/ folder contains production files
```
