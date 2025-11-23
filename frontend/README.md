# ESRGAN Interface - Frontend

Next.js frontend application for the ESRGAN image upscaling service.

---

## Features

- **Image Upload**: Drag-and-drop or click to upload images (PNG, JPEG, WebP)
- **Real-time Progress**: Server-Sent Events (SSE) for live processing updates
- **Scale Selection**: Choose between 2x or 4x upscaling
- **Image Comparison**: Side-by-side view of original and upscaled images
- **Processing Metrics**: Detailed timing and dimension information
- **Responsive Design**: Works on desktop and mobile devices

---

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **State Management**: React hooks
- **API Communication**: Fetch API + EventSource (SSE)

---

## Project Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── api/esrgan/            # API proxy routes
│   ├── page.tsx               # Main application page
│   ├── layout.tsx             # Root layout
│   └── globals.css            # Global styles
├── components/                 # React components
│   ├── ui/                    # Base UI components
│   ├── ImageUpload.tsx        # File upload component
│   ├── ImagePreview.tsx       # Image comparison view
│   ├── ProcessingStatus.tsx   # Status indicator
│   ├── ProgressBar.tsx        # Progress bar
│   ├── ProcessingStages.tsx   # Pipeline stages view
│   └── ProcessingMetadata.tsx # Metrics display
├── lib/                        # Utility functions
│   ├── api.ts                 # Backend API client
│   └── utils.ts               # Helper functions
└── types/                      # TypeScript definitions
    ├── api.ts                 # API types
    └── props.ts               # Component prop types
```

---

## Getting Started

### Prerequisites

- Node.js 20+ installed
- Backend service running on port 8000

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create `.env.local`:

```env
BACKEND_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

---

## API Integration

### Backend Communication

The frontend communicates with the FastAPI backend through:

1. **Next.js API Routes** (`/api/esrgan/*`) - Proxy for POST requests
2. **Direct SSE Connection** - Real-time progress updates via EventSource

### Endpoints Used

- `POST /upscale` - Upload and process image
- `GET /progress/{job_id}` - SSE stream for progress updates (direct connection)
- `GET /scales` - Available scaling factors
- `GET /health` - Backend health check

---

## Component Architecture

### Main Page (`app/page.tsx`)

Orchestrates the entire application flow:

- File upload and validation
- Scale selection (2x or 4x)
- Progress monitoring via SSE
- Image preview and comparison
- Metrics display

### Core Components

**`ImageUpload`** - Handles file selection with drag-and-drop  
**`ImagePreview`** - Side-by-side comparison of original and upscaled images  
**`ProcessingStatus`** - Shows current processing stage with status messages  
**`ProgressBar`** - Visual progress indicator with percentage  
**`ProcessingStages`** - Displays all 9 processing stages with status icons  
**`ProcessingMetadata`** - Shows timing metrics and image dimensions

### UI Components

Base components in `components/ui/`:

- `Button` - Styled button with variants
- `Card` - Container with header and content sections
- `Progress` - Animated progress bar
- `Label` - Form labels
- `Alert` - Status and error messages
- `RadioGroup` - Scale selection radio buttons

---

## State Management

State is managed at the page level using React hooks:

- `selectedFile` - Current uploaded file
- `scale` - Selected upscaling factor (2x or 4x)
- `isProcessing` - Processing state flag
- `currentStage` - Current processing stage
- `processedImage` - Base64-encoded result image
- `metadata` - Processing metrics
- `error` - Error messages
- `progressConnection` - EventSource connection

---

## Error Handling

Errors are caught and displayed at multiple levels:

1. **File Validation** - Client-side validation before upload
2. **Upload Errors** - API request failures
3. **SSE Connection Errors** - Progress stream issues
4. **Backend Errors** - Processing failures from FastAPI

---

## Performance Considerations

- **Image Preview** - Uses `URL.createObjectURL` for efficient preview
- **SSE Polling** - 300ms interval for smooth progress updates
- **Connection Cleanup** - EventSource connections properly closed
- **Memory Management** - Preview URLs revoked when no longer needed

---

## Deployment

### Vercel (Recommended)

```bash
vercel deploy
```

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Environment Variables

Set `BACKEND_URL` to your production backend URL.

---

## Development Guidelines

### Code Style

- Use TypeScript for all files
- Follow Next.js App Router conventions
- Separate concerns (types, components, utilities)
- Use "use client" directive only when needed

### Component Design

- Props defined in `types/props.ts`
- Use functional components with hooks
- Keep components focused and reusable
- Include proper TypeScript types

### API Client

- All backend communication in `lib/api.ts`
- Proper error handling and type safety
- SSE connection management
- File validation before upload

---

## Troubleshooting

### SSE Connection Issues

If progress updates aren't working:

1. Check CORS configuration in backend
2. Verify backend `/progress/{job_id}` endpoint
3. Check browser console for SSE errors
4. Ensure backend URL is correct

### Upload Failures

1. Verify file type (PNG, JPEG, WebP only)
2. Check file size (max 20MB)
3. Ensure backend is running
4. Check network tab for API errors

### Build Errors

1. Run `npm install` to ensure dependencies are installed
2. Check TypeScript errors with `npm run build`
3. Verify all imports are correct
4. Ensure Node.js version is 20+

---

## License

See root project LICENSE file.
