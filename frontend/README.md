# Commission Calculator Pro - Frontend

This is the modern React/Next.js frontend for Commission Calculator Pro, designed to work with the FastAPI backend.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open [http://localhost:3000](http://localhost:3000) in your browser**

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js app directory
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Main page with tabs
│   │   └── globals.css   # Global styles
│   ├── components/       # React components
│   │   ├── Dashboard/    # Dashboard components
│   │   ├── CompanySetup/ # Company setup components
│   │   └── ...          # Other feature components
│   ├── lib/             # Libraries and utilities
│   │   ├── api/         # API integration layer
│   │   └── utils.ts     # Utility functions
│   ├── types/           # TypeScript type definitions
│   └── contexts/        # React contexts
├── public/              # Static assets
├── package.json         # Dependencies
└── next.config.js       # Next.js configuration
```

## 🔗 API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000` by default. The API integration is handled through:

- **API Client** (`/src/lib/api/client.ts`): Axios instance with interceptors
- **Services** (`/src/lib/api/services/`): Organized by domain (employees, commissions, etc.)
- **React Query**: For caching and state management

## 🎨 Key Features

### Dashboard
- Real-time metrics and KPIs
- Revenue trends visualization
- Top performer rankings
- Current pay period status

### Company Setup
- Employee management (CRUD)
- Business unit configuration
- Pay period generation
- Advanced settings

### Data Management
- File upload (CSV/Excel)
- Data validation
- Template downloads
- Manual overrides

### Commission Calculator
- Pay period selection
- Employee selection
- Real-time calculation
- Results preview

### Reports
- Detailed commission breakdowns
- Revenue analysis
- Employee performance
- Export functionality

## 🛠️ Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query + Context API
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts
- **UI Components**: Headless UI
- **Icons**: Heroicons

## 📝 Development Notes

### State Management
Global state is managed through Context API (`AppStateContext`) for:
- Current pay period
- Loaded data (employees, revenue, etc.)
- Commission results
- UI state

### API Error Handling
The API client includes automatic error handling with toast notifications for:
- Validation errors (422)
- Authentication errors (401)
- Network errors
- Server errors (500)

### File Uploads
File uploads are handled with progress tracking and validation on both client and server sides.

## 🚀 Building for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

## 📋 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_APP_NAME` | Application name | `Commission Calculator Pro` |
| `NEXT_PUBLIC_APP_VERSION` | App version | `2.0.0` |

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch
```

## 📚 Component Development

Use Storybook for component development:

```bash
npm run storybook
```

## 🎯 Next Steps for Vercel Team

1. **Complete Component Implementation**: The stub components need full implementation
2. **Add Form Validation**: Implement Zod schemas for all forms
3. **Enhance Error Handling**: Add error boundaries and better user feedback
4. **Implement File Upload**: Complete the file upload components
5. **Add Tests**: Write unit and integration tests
6. **Optimize Performance**: Add virtualization for large lists
7. **Mobile Responsiveness**: Ensure all components work on mobile
8. **Accessibility**: Add ARIA labels and keyboard navigation

---

Built with ❤️ for efficient commission management