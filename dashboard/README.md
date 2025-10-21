# Admin Dashboard

This directory contains the Admin Dashboard MVP implementation for the Telegram Complaint Management System.

## Files

- `login.html` - Authentication page with modern UI design
- `index.html` - Main dashboard with complaint management interface

## Features

### Login Page (`login.html`)
- Clean, modern design with Tailwind CSS
- Responsive login form
- JWT token authentication
- Error handling and loading states
- Automatic redirect to dashboard

### Main Dashboard (`index.html`)
- Comprehensive complaint list with pagination
- Advanced filtering (status, hostel, category, severity)
- Sortable columns
- Complaint detail modal
- Status and assignment management
- Real-time data refresh
- Mobile-responsive design

## Access

Once the FastAPI server is running, access the dashboard at:
- Login: `http://localhost:8000/dashboard/login.html`
- Dashboard: `http://localhost:8000/dashboard/index.html`

## Design Principles

- **Modern UI**: Clean, professional interface with consistent styling
- **Responsive**: Mobile-first design that works on all screen sizes
- **Intuitive**: Logical navigation and clear information hierarchy
- **Accessible**: Proper ARIA labels and keyboard navigation
- **Fast**: Optimized loading and smooth interactions

## Technical Details

- Pure HTML/CSS/JavaScript (no frameworks)
- Tailwind CSS for styling
- Fetch API for backend communication
- JWT token authentication
- SessionStorage for token persistence
- Responsive design with CSS Grid and Flexbox
