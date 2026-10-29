# E-Commerce Sales & Web Analytics Dashboard

A production-ready, web-based analytics application that enables users to upload e-commerce transaction or web activity datasets in CSV or Excel formats and automatically generate comprehensive business insights.

## Features

- **Single Website Application**: Flask serves both backend API and React frontend from one server
- **Automated Data Processing**: Upload CSV/Excel files and automatically validate, clean, and analyze data
- **Flexible Column Support**: Handles various column naming conventions (Date/SalesDate, Price/UnitPrice)
- **Dual Dataset Support**: Handles both transaction data and web analytics data
- **Interactive Dashboard**: Real-time KPIs, charts, and data visualizations
- **Customer Analytics**: Customer segmentation, spending analysis, and leaderboards
- **Conversion Funnel**: Track customer journey from visitors to purchases
- **Real-time Filtering**: Filter data by date, category, product, payment mode, device, and traffic source
- **Data Preview**: View cleaned and processed data with pagination

## Technology Stack

- **Frontend**: React.js with React Router, Recharts for visualizations
- **Backend**: Flask with Flask-CORS for API endpoints
- **Data Processing**: Pandas for data parsing, cleaning, and analysis
- **File Processing**: Native Pandas support for CSV and Excel files

## Project Structure

```
ecommerce-analytics-dashboard/
├── backend/
│   ├── app.py                 # Flask application and API endpoints
│   ├── data_processor.py      # Data processing and analysis logic
│   ├── requirements.txt       # Python dependencies
│   └── temp_uploads/          # Temporary file storage (auto-created)
├── frontend/
│   ├── dist/                  # Built React application (served by Flask)
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── KPICards.jsx
│   │   │   ├── SalesCharts.jsx
│   │   │   ├── CustomerAnalytics.jsx
│   │   │   ├── WebAnalytics.jsx
│   │   │   └── FilterPanel.jsx
│   │   ├── context/           # React Context for state management
│   │   │   └── FilterContext.jsx
│   │   ├── pages/             # Page components
│   │   │   ├── Upload.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── DataPreview.jsx
│   │   ├── utils/             # Utility functions
│   │   │   └── api.js         # API client
│   │   ├── App.jsx            # Main App component
│   │   └── App.css            # Global styles
│   ├── vite.config.js         # Vite configuration
│   └── package.json           # Node.js dependencies
├── sample_transaction_data.csv    # Sample transaction dataset
├── sample_web_analytics_data.csv  # Sample web analytics dataset
└── README.md
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### Setup

1. Navigate to the project directory:
```bash
cd ecommerce-analytics-dashboard
```

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
cd ..
```

3. Install Node.js dependencies and build the frontend:
```bash
cd frontend
npm install
npm run build
cd ..
```

4. Start the application:
```bash
cd backend
python app.py
```

The application will run on `http://localhost:5000`

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Upload a CSV or Excel file containing your e-commerce data
3. The system will automatically:
   - Validate the file format and required columns
   - Clean and process the data
   - Generate analytics and visualizations
4. Explore the dashboard with:
   - KPI cards showing key metrics
   - Interactive charts for sales trends and category performance
   - Customer segmentation and analytics
   - Conversion funnel for web analytics
   - Real-time filtering capabilities
5. View the processed data in the Data Preview page

## Dataset Requirements

### Transaction Dataset Required Columns:
- TransactionID, CustomerID, ProductID, ProductName
- Category, Quantity, Price/UnitPrice, TotalAmount
- Date/SalesDate, PaymentMode

### Web Analytics Dataset Required Columns:
- SessionID, EventType, Timestamp, ProductID
- CustomerID, Device, TrafficSource, SessionDuration

**Note**: The system is flexible with column naming and can handle variations like:
- Date or SalesDate for date columns
- Price or UnitPrice for price columns
- Various date formats (DD-MM-YY, YYYY-MM-DD, etc.)

## Sample Data

Two sample datasets are provided for testing:
- `sample_transaction_data.csv` - Sample e-commerce transaction data
- `sample_web_analytics_data.csv` - Sample web analytics event data

## API Endpoints

- `POST /api/upload` - Upload and process a file
- `GET /api/kpis/:sessionId` - Get KPI metrics
- `GET /api/charts/:sessionId` - Get chart data
- `GET /api/customers/:sessionId` - Get customer analytics
- `GET /api/web-analytics/:sessionId` - Get web analytics
- `GET /api/data-preview/:sessionId` - Get data preview
- `DELETE /api/session/:sessionId` - Delete a session

## Features Breakdown

### Upload Page
- Drag-and-drop file upload
- File format validation (CSV, Excel)
- File size validation (max 50MB)
- Real-time error messages
- Flexible column name matching

### Dashboard Page
- KPI cards with real-time updates
- Sales analytics charts (Revenue Trend, Category Sales, Top Products)
- Customer analytics (Segmentation, Leaderboard)
- Web analytics (Conversion Funnel, Traffic Sources, Device Distribution)
- Real-time filter panel

### Data Preview Page
- File information display
- Detected columns listing
- Paginated data table
- Navigation back to dashboard

## Responsive Design

The application is fully responsive and works on:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (320px - 767px)

## Error Handling

- File format validation
- Flexible column schema validation
- Data cleaning error handling
- API error handling with user-friendly messages
- Network error handling
- Support for various date formats

## Security Considerations

- Temporary file storage with automatic cleanup
- File size limits to prevent DoS attacks
- CORS enabled for cross-origin requests
- No sensitive data logging

## Development

### Running Tests
To test the application:
1. Build the frontend: `cd frontend && npm run build`
2. Start the server: `cd backend && python app.py`
3. Upload sample datasets or your own data
4. Verify all visualizations load correctly
5. Test filter functionality
6. Check responsive design on different screen sizes

### Development Mode

For development with hot-reload:
1. Start backend: `cd backend && python app.py`
2. Start frontend dev server: `cd frontend && npm run dev`
3. Access frontend at `http://localhost:5173` (API proxied to backend)

### Rebuilding for Production

After making frontend changes:
```bash
cd frontend
npm run build
cd ..
# Restart backend to serve new build
cd backend
python app.py
```

### Production Deployment

For production, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Application won't start
- Ensure all Python dependencies are installed
- Check that port 5000 is not in use
- Verify the frontend has been built (`npm run build`)

### File upload errors
- Verify CSV/Excel file format matches requirements
- Check that required columns are present (flexible naming supported)
- Ensure file size is under 50MB
- Check date format consistency

### Data processing issues
- The system handles various date formats automatically
- Column names are matched flexibly (Price/UnitPrice, Date/SalesDate)
- Check the error messages for specific column requirements

### Frontend not updating
- Rebuild the frontend: `cd frontend && npm run build`
- Restart the backend server
- Clear browser cache

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions, please refer to the project documentation or contact the development team.
