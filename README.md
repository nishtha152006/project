# Rupee - Smart Food Demand Forecasting and Surplus Redistribution System

A comprehensive web-based system to help food-service kitchens predict meal demand, manage food preparation, calculate surplus food availability, and redistribute safe surplus food to eligible recipients.

## Project Objective

The system addresses food waste in institutional kitchens by:
1. Predicting meal demand based on attendance, weather, and event data
2. Recommending optimal preparation quantities
3. Calculating food surplus accurately
4. Checking food safety based on storage conditions
5. Redistributing safe surplus food to eligible recipients
6. Tracking impact (food saved, cost saved, carbon saved)

## Features

### ✓ Complete
- **Three User Roles**: Admin, Kitchen Staff, Recipient
- **Role-Based Access Control**: Each role has dedicated dashboard
- **Professional Login System**: Secure backend validation
- **Kitchen Staff Dashboard**: 
  - Data entry for forecasts and actual quantities
  - Meal planning calendar (fully functional, interactive)
  - Current location tracking with map display
  - Automatic demand forecasting
- **Admin Dashboard**:
  - Real-time food status monitoring
  - Recipient request management and approval
  - Functional charts (Chart.js) using real database data
  - Impact metrics display
- **Recipient Dashboard**:
  - View available safe surplus food
  - Request surplus food
  - Track request status
- **REST APIs**: 8+ endpoints for all operations
- **SQLite Database**: Centralized data storage with proper schema
- **Demand Forecasting**: 
  - Attendance factor (1.2)
  - Weather factor (0.8-1.2)
  - Event factor (0.8-1.5)
  - Historical factor (configurable)
  - Safety margin (15%)
- **Food Safety Checks**: Based on temperature and storage time
- **Surplus Calculation**: Prepared - Consumed (never negative)
- **Functional Charts**:
  - Predicted vs Actual vs Consumed
  - Surplus Over Time
  - Recipient Requests by Status
  - Redistribution Impact
- **Impact Metrics**: Food saved, cost saved, carbon saved
- **Responsive Design**: Works on desktop and mobile
- **Error Handling**: In-dashboard error messages (no alerts)
- **Comprehensive Tests**: 17+ pytest tests covering all features
- **Render Deployment Ready**: Configured for production deployment

## Technologies

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Python Flask
- **Database**: SQLite
- **Charts**: Chart.js
- **Testing**: pytest
- **Deployment**: Render compatible

## Project Structure

```
rupee-project/
├── app.py                    # Flask application with all routes and APIs
├── database.py               # Database initialization and schema
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── templates/
│   ├── login.html           # Login page
│   ├── admin.html           # Admin dashboard
│   ├── kitchen.html         # Kitchen staff dashboard
│   └── recipient.html       # Recipient dashboard
│
├── static/
│   ├── css/
│   │   └── style.css        # Unified styling for all dashboards
│   │
│   └── js/
│       ├── common.js        # Shared functions (fetchJson, auth, etc.)
│       ├── login.js         # Login page logic
│       ├── admin.js         # Admin dashboard logic
│       ├── kitchen.js       # Kitchen dashboard logic
│       └── recipient.js     # Recipient dashboard logic
│
├── database/
│   └── rupee.db             # SQLite database (auto-created)
│
└── tests/
    └── test_main.py         # Comprehensive test suite
```

## Database Schema

### Users Table
```
id (PRIMARY KEY)
username (UNIQUE)
password
role (admin | kitchen | recipient)
is_active
created_at
```

### Recipients Table
```
id (PRIMARY KEY)
name
eligibility_status (eligible | ineligible)
is_active
created_at
```

### Forecasts Table
```
id (PRIMARY KEY)
forecast_date
expected_attendance
weather_conditions
event_type
predicted_demand
recommended_quantity
created_at
updated_at
```

### Food Surplus Table
```
id (PRIMARY KEY)
forecast_id (FOREIGN KEY → forecasts)
prepared_quantity
consumed_quantity
surplus_quantity
storage_time
storage_temperature
safety_status (safe | unsafe)
status (available | redistributed | disposed)
created_at
updated_at
```

### Recipient Requests Table
```
id (PRIMARY KEY)
recipient_id (FOREIGN KEY → recipients)
surplus_id (FOREIGN KEY → food_surplus)
quantity
status (pending | approved | rejected)
created_at
updated_at
```

## API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/verify-session` - Verify current session

### Kitchen Staff
- `POST /api/kitchen/surplus` - Save forecast and surplus data
- `GET /api/kitchen/latest` - Get latest forecast and surplus record

### Admin
- `GET /api/admin/dashboard` - Get current food status and pending requests
- `GET /api/admin/chart-data` - Get data for analytics charts
- `POST /api/admin/request/approve` - Approve recipient request

### Recipient
- `GET /api/recipient/available-food` - Get safe available surplus food
- `POST /api/recipient/request` - Create food request
- `GET /api/recipient/my-requests` - Get recipient's own requests

### Impact
- `GET /api/impact/calculations` - Get impact metrics

## Frontend Architecture

### Common.js
Provides shared utilities:
- `fetchJson()` - Universal API fetch wrapper
- `getDetectedRole()` - Get current user's role
- `verifyAuthentication()` - Validate user session
- `showError()` - Display error messages in dashboard
- `showSuccess()` - Display success messages
- `handleLogout()` - Handle logout for all dashboards

### Kitchen.js
- `loadKitchenData()` - Initialize kitchen dashboard
- `buildKitchenForm()` - Setup form event listeners
- `calculateAndDisplayDemand()` - Auto-calculate predicted demand
- `handleKitchenFormSubmit()` - Process form submission
- `loadLatestRecord()` - Display latest kitchen data
- `setupCalendar()` - Initialize meal planning calendar
- `renderCalendar()` - Render calendar for selected month
- `setupLocation()` - Initialize geolocation
- Global variables: `selectedCalendarDate`, `calendarDate`

### Admin.js
- `loadAdminData()` - Initialize admin dashboard
- `loadDashboardData()` - Fetch and display current status
- `displayPendingRequests()` - Show pending requests table
- `approveRequest()` - Handle request approval
- `loadChartData()` - Fetch chart data from API
- `renderCharts()` - Render all four charts using Chart.js
- `loadImpactMetrics()` - Display impact calculations
- Chart instances: `demandChart`, `surplusChart`, `requestsChart`, `redistributionChart`

### Recipient.js
- `loadRecipientData()` - Initialize recipient dashboard
- `loadRecipientProfile()` - Display recipient information
- `loadAvailableFood()` - Fetch safe available surplus
- `displayAvailableFood()` - Show food cards
- `openRequestModal()` - Open request dialog
- `setupRequestModal()` - Setup modal events and form
- `loadMyRequests()` - Display recipient's requests
- `displayMyRequests()` - Render requests table

## Demand Forecasting Logic

The system uses a multiplicative factor model:

```
predicted_demand = expected_attendance × attendance_factor × weather_factor × event_factor × historical_factor

Where:
- attendance_factor = 1.2 (each person consumes ~1.2 portions)
- weather_factor = 0.8 to 1.2 (affects appetite)
  - sunny: 0.9
  - cloudy: 1.0
  - rainy: 1.1
  - cold: 1.2
  - hot: 0.8
- event_factor = 0.8 to 1.5 (affects demand)
  - regular: 1.0
  - festival: 1.5
  - exam: 1.2
  - holiday: 0.8
  - special: 1.4
- historical_factor = customizable (default: 1.0)

recommended_quantity = predicted_demand × 1.15 (15% safety margin)
```

### Example Calculation
- Attendance: 200 people
- Weather: Sunny (0.9)
- Event: Regular (1.0)

```
predicted_demand = 200 × 1.2 × 0.9 × 1.0 × 1.0 = 216 kg
recommended_quantity = 216 × 1.15 = 248.4 kg
```

## Surplus Calculation

```
surplus_quantity = prepared_quantity - consumed_quantity

If result < 0:
    surplus_quantity = 0 (never negative)
```

### Example
```
Prepared: 500 kg
Consumed: 400 kg
Surplus: 100 kg
```

## Food Safety Logic

Safety is determined by storage temperature and time:

```
Frozen (-18°C or below):
    Maximum storage: 30 days → SAFE

Refrigerated (4-8°C):
    Maximum storage: 24 hours → SAFE

Room Temperature (20-25°C):
    Maximum storage: 2 hours → SAFE

Otherwise → UNSAFE
```

Food marked as UNSAFE:
- Cannot be requested by recipients
- Not displayed in recipient's available food list
- Must be disposed

## Calendar Functionality

The meal planning calendar is fully interactive:
- Displays current month and year
- Previous/Next month navigation (doesn't reload page)
- Shows all days of the month in grid layout
- Highlights today's date
- Allows clicking any date to select it
- Selected date automatically fills forecast_date input
- Calendar state preserved during page use
- Only one `renderCalendar()` function (no duplicates)
- Only one `setupCalendar()` function (no duplicates)

## Location Feature

- Uses HTML5 Geolocation API
- Requests browser permission
- Returns latitude and longitude
- Embeds OpenStreetMap iframe showing location
- Graceful error handling if permission denied
- Dashboard remains functional if location unavailable

## Admin Dashboard Charts

All charts use real database data via `/api/admin/chart-data`:

1. **Predicted vs Actual vs Consumed**
   - Line chart showing three metrics over time
   - Helps identify over/under-preparation

2. **Food Surplus Over Time**
   - Bar chart of surplus quantity per day
   - Shows redistribution potential

3. **Recipient Requests by Status**
   - Doughnut chart of pending/approved/rejected counts
   - Visual request status distribution

4. **Redistribution Impact**
   - Bar chart comparing redistributed vs total surplus
   - Shows redistribution effectiveness

## Impact Metrics

Calculated from approved/redistributed food:

```
Food Saved = Sum of all approved request quantities (kg)

Cost Saved = Food Saved × 50 ₹/kg
(Assumption: ₹50 cost per kg - can be adjusted)

Carbon Saved = Food Saved × 0.5 kg CO₂/kg
(Assumption: 0.5 kg CO₂ per kg of food - can be adjusted)
```

### Example
```
Food Saved: 250 kg
Cost Saved: 250 × 50 = ₹12,500
Carbon Saved: 250 × 0.5 = 125 kg CO₂ equivalent
```

## Demo Credentials

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Admin | admin | admin123 | Admin Dashboard |
| Kitchen | kitchen | kitchen123 | Kitchen Dashboard |
| Recipient 1 | recipient1 | recipient123 | Recipient Dashboard |
| Recipient 2 | recipient2 | recipient123 | Recipient Dashboard |

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Steps

1. **Clone or download the project**
```bash
cd rupee-project
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **The database will be automatically created when you run the app**

## Running the Application

### Development Mode
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Production Mode (Render)
```bash
python app.py
```

The app automatically uses `PORT` environment variable if set (defaults to 5000).

## Running Tests

```bash
pytest tests/test_main.py -v
```

### Test Coverage

The test suite includes:

1. **Database Tests**
   - Database initialization

2. **Authentication Tests**
   - Admin login
   - Kitchen staff login
   - Recipient login
   - Invalid login handling

3. **Kitchen API Tests**
   - Save forecast and surplus data
   - Surplus calculation (500 - 400 = 100)
   - Food safety logic
   - Get latest record

4. **Admin API Tests**
   - View dashboard
   - Retrieve chart data
   - Approve requests
   - Prevent negative surplus
   - Prevent duplicate approvals

5. **Recipient API Tests**
   - View available food
   - Create requests
   - Hide unsafe food from recipients

6. **End-to-End Test**
   - Complete workflow: Kitchen entry → Admin view → Recipient request → Admin approval → Surplus reduction

7. **Impact Metrics Tests**
   - Impact calculations

## Deployment to Render

### Prerequisites
- GitHub account
- Render account (render.com)

### Steps

1. **Push project to GitHub**
```bash
git init
git add .
git commit -m "Initial Rupee project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rupee.git
git push -u origin main
```

2. **Create a Render Web Service**
- Go to render.com
- Click "New +"
- Select "Web Service"
- Connect your GitHub repository
- Select the Rupee project repository

3. **Configure Settings**
- **Name**: rupee-app
- **Environment**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`
- **Python Version**: 3.9+

4. **Add Environment Variables** (Optional)
- `SECRET_KEY`: Your secret key (for production)
- `PORT`: Will be automatically provided by Render

5. **Deploy**
- Click "Deploy"
- Render will build and start your application
- Your app will be live at `https://rupee-app.onrender.com`

### Database Note
SQLite database is created in the `database/` directory. On Render, this will be in the ephemeral filesystem, so data will be lost on redeploy. For production, consider migrating to PostgreSQL.

## Error Handling

### Frontend
- Errors displayed in-dashboard, not via alert()
- `showError()` function displays errors for 5 seconds
- `showSuccess()` displays success messages for 3 seconds
- Dashboard remains visible and functional after errors

### Backend
- All Flask endpoints return JSON responses
- Appropriate HTTP status codes (200, 400, 401, 404, 500)
- Useful error messages for debugging
- Database errors handled safely

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Code Quality

- **No Duplicate Functions**: Each JavaScript function defined once
- **Single DOMContentLoaded**: One main event listener per page
- **No Page Blinking**: Charts and calendars don't reload page
- **Clean Architecture**: Separation of concerns between files
- **Error Messages**: Clear, user-friendly messages
- **Responsive Design**: Mobile-first CSS approach

## Performance Considerations

- Chart.js efficiently renders multiple datasets
- Calendar uses only DOM manipulation (no page reload)
- API responses optimized with database indexes
- Lazy loading for maps (OpenStreetMap iframe)
- Session-based authentication (no redundant checks)

## Security Notes

### Current Implementation (Development)
- Plain text password comparison (for demo)
- Session-based authentication via Flask

### Recommended for Production
- Use bcrypt for password hashing
- Implement HTTPS
- Add CSRF protection
- Use secure session cookies
- Implement rate limiting
- Add input validation and sanitization
- Use environment variables for secrets

## Troubleshooting

### Database Issues
```bash
# Reinitialize database
python -c "from database import init_db; init_db()"
```

### Port Already in Use
```bash
# Use a different port
PORT=5001 python app.py
```

### Module Not Found
```bash
# Ensure dependencies are installed
pip install -r requirements.txt
```

### Tests Failing
```bash
# Run with verbose output
pytest tests/test_main.py -v
```

## File Sizes and Stats

- **Total Files**: 11
- **HTML Templates**: 4 files (~1.5 KB each)
- **JavaScript Files**: 5 files (~10 KB total)
- **CSS File**: 1 file (~15 KB)
- **Python Files**: 2 files (~25 KB total)
- **Tests**: 1 file (~30 KB)
- **Total Size**: ~150 KB (excluding dependencies)

## Future Enhancements (Optional)

1. **Multi-location support**: Multiple kitchens in one system
2. **User notifications**: Email/SMS alerts for requests
3. **Historical analysis**: Trend analysis and predictions
4. **Mobile app**: Native iOS/Android apps
5. **PostgreSQL migration**: For production deployment
6. **Advanced analytics**: Machine learning-based forecasting
7. **Batch exports**: CSV/PDF reports
8. **Audit logs**: Complete activity tracking
9. **Food item categorization**: Track different food types
10. **Nutritional tracking**: Calorie and nutrient calculations

## License

This project is created as a B.Tech CSE college project.

## Support

For issues or questions, please refer to:
- README.md (this file)
- Code comments in Python and JavaScript files
- Test file for usage examples
- Flask documentation: https://flask.palletsprojects.com/
- Chart.js documentation: https://www.chartjs.org/

## Author

Rupee Development Team - College Project

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Ready for Production Demonstration
