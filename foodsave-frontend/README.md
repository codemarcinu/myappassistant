# FoodSave AI Frontend

This is the Next.js/TypeScript implementation of the FoodSave AI frontend, refactored from the original Streamlit prototype.

## Project Structure

The project follows a modular architecture with clear separation of concerns:

```
foodsave-frontend/
├── public/                  # Static assets
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── layout.tsx       # Root layout component
│   │   ├── page.tsx         # Home page (redirects to dashboard)
│   │   ├── dashboard/       # Dashboard module
│   │   ├── chat/            # Chat module
│   │   ├── shopping/        # Shopping module
│   │   └── cooking/         # Cooking module
│   ├── components/          # Reusable React components
│   │   ├── ui/              # UI components (Button, Card, etc.)
│   │   ├── dashboard/       # Dashboard-specific components
│   │   ├── chat/            # Chat-specific components
│   │   ├── shopping/        # Shopping-specific components
│   │   ├── cooking/         # Cooking-specific components
│   │   └── common/          # Shared components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utility functions and libraries
│   ├── services/            # API services
│   └── types/               # TypeScript type definitions
```

## Features

- **Dashboard**: Central hub with weather information and navigation to other modules
- **Chat**: Conversational interface with AI assistant
- **Shopping**: Receipt upload, product management, and shopping assistant
- **Cooking**: Pantry management and cooking assistant

## Technology Stack

- **Next.js**: React framework with server-side rendering and API routes
- **TypeScript**: Static typing for better developer experience
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API requests

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies:

```bash
cd foodsave-frontend
npm install
# or
yarn install
```

3. Create a `.env.local` file with the following variables:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

4. Start the development server:

```bash
npm run dev
# or
yarn dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Building for Production

```bash
npm run build
# or
yarn build
```

## Running in Production Mode

```bash
npm start
# or
yarn start
