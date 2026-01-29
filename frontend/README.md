# Care Coordinator Frontend

React + TypeScript + Vite + Tailwind CSS + Socket.IO

## Setup

```bash
# Install dependencies
npm install

# Copy env file
cp .env.example .env

# Start dev server
npm run dev
```

Frontend runs on http://localhost:3000

## Requirements

- Backend API running on port 5000
- Agent WebSocket server running on port 5001

## Features

- Real-time chat with AI agent via WebSocket
- Patient information panel
- Debug mode for booking progress
- Session persistence with localStorage
- Reset chat and next patient functions
