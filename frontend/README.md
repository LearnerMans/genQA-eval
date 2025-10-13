# 🎨 RAG Eval Core - Frontend Interface

A modern React-based user interface for the **RAG Eval Core** platform, providing an intuitive way to manage projects, run tests, and visualize results.

## 🌟 What This Interface Does

The React frontend serves as the **control center** for your RAG evaluation workflows, offering:

### Project Management
- **Create & Organize Projects**: Manage multiple evaluation projects
- **Visual Project Dashboard**: See all projects at a glance
- **Easy Navigation**: Seamless movement between projects and tests

### Test Configuration & Execution
- **Test Setup**: Configure chunking strategies, AI models, and parameters
- **Document Upload**: Upload files directly through the web interface
- **URL Processing**: Add web content for evaluation
- **Real-time Progress**: Watch document processing as it happens

### Side-by-Side Model Comparison
- **A/B Testing Interface**: Compare two AI models simultaneously
- **Interactive Results**: Click to expand/collapse prompt previews
- **Visual Metrics**: Easy-to-read performance comparisons
- **Detailed Analysis**: Deep dive into specific Q&A pairs

### Advanced Prompt Management
- **Prompt Creation**: Build and edit prompts with variable insertion
- **Live Preview**: See how prompts will appear before using them
- **Variable Management**: Easy insertion of `{{query}}` and `{{chunks}}` variables
- **Prompt Library**: Save and reuse effective prompts

## 🚀 Getting Started

### Prerequisites
- Node.js 16+
- The RAG Eval Core backend server running

### Installation & Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Open the Interface**
   - Main Interface: http://localhost:5173
   - Backend API: http://localhost:8000

## 🎯 Key Features

### Modern UI Components
- **Responsive Design**: Works on desktop and mobile devices
- **Dark/Light Theme**: Easy on the eyes in any environment
- **Intuitive Navigation**: Clear tabs and organized sections
- **Loading States**: Visual feedback during operations

### Interactive Elements
- **Dropdown Selectors**: Easy test run selection with search
- **Expandable Sections**: Click to reveal prompt text and details
- **Progress Indicators**: Visual feedback for all operations
- **Modal Dialogs**: Clean interfaces for complex operations

### Real-Time Updates
- **Live Progress**: See document processing in real-time
- **Status Indicators**: Know exactly what's happening
- **Error Handling**: Clear feedback when things go wrong
- **Success Notifications**: Confirmation when operations complete

## 📱 Interface Sections

### Projects Page
- **Project Cards**: Visual representation of all projects
- **Quick Actions**: Fast access to common operations
- **Status Overview**: See which projects are active

### Test Page
- **Run Selection**: Choose which test runs to compare
- **Prompt Previews**: Expandable prompt text with formatting
- **Results Table**: Comprehensive Q&A results with metrics
- **Comparison Mode**: Side-by-side AI model evaluation

### Prompts Management
- **Prompt Editor**: Rich text editing with variable insertion
- **Preview Mode**: See exactly how prompts will execute
- **Validation**: Real-time feedback on prompt completeness
- **Template Library**: Save and reuse successful prompts

## 🛠️ Technical Stack

- **React 18**: Modern React with hooks and concurrent features
- **Vite**: Fast build tool with HMR (Hot Module Replacement)
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Custom Hooks**: Reusable logic for API calls and state management
- **Toast Notifications**: User feedback for operations
- **Responsive Grid**: Flexible layouts that adapt to screen size

## 🔧 Development

### Available Scripts
- `npm run dev` - Start development server with HMR
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint for code quality

### Code Organization
```
src/
├── components/     # Reusable UI components
├── pages/         # Main application pages
├── services/      # API communication layer
├── assets/        # Static assets (images, icons)
└── App.jsx        # Main application component
```

## 🎨 Customization

### Styling
- **Tailwind Classes**: Utility-first approach for consistent styling
- **Custom Colors**: Primary, accent, and semantic color schemes
- **Responsive Breakpoints**: Mobile-first responsive design
- **Dark Mode Support**: Theme switching capabilities

### Components
- **Modular Design**: Each component has a single responsibility
- **Prop Interfaces**: TypeScript-ready component APIs
- **Accessibility**: ARIA labels and keyboard navigation
- **Performance**: Optimized rendering and state management

## 🚨 Troubleshooting

### Common Issues

1. **Backend Connection Issues**
   - Ensure the RAG Eval Core backend is running on port 8000
   - Check that CORS is properly configured
   - Verify API endpoints are accessible

2. **Build Issues**
   - Clear node_modules and reinstall if dependencies are corrupted
   - Check that all peer dependencies are installed
   - Verify Node.js version compatibility

3. **Runtime Errors**
   - Check browser console for detailed error messages
   - Verify API responses match expected data structures
   - Ensure WebSocket connections are allowed

## 📚 Learn More

- **App Overview**: `APP_OVERVIEW.md` - Complete application explanation
- **Backend Documentation**: `README.md` - API and backend features
- **Getting Started**: `GETTING_STARTED.md` - Step-by-step setup guide

## 🔮 Future Enhancements

- **Real-time Collaboration**: Multi-user editing and monitoring
- **Advanced Visualizations**: Charts and graphs for results
- **Export Features**: PDF reports and data export
- **Mobile Optimization**: Enhanced mobile experience
- **Plugin System**: Extensible component architecture

---

**Happy evaluating!** 🎉 The React interface makes RAG evaluation accessible to everyone, from developers to business users.
