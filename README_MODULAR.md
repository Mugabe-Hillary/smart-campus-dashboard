# Smart Campus Dashboard - Modular Architecture

## 🏗️ Architecture Overview

The Smart Campus Dashboard has been refactored into a modular architecture for better maintainability, scalability, and code organization.

### 📁 Project Structure

```
pi_server_3/
├── dashboard_modular.py      # Main application entry point
├── dashboard.py             # Original monolithic version
├── config.py               # Configuration settings
├── requirements-modular.txt # Dependencies for modular version
├── auth/                   # Authentication module
│   ├── __init__.py
│   ├── user_manager.py     # User management logic
│   └── auth_ui.py         # Authentication UI components
├── database/              # Database module
│   ├── __init__.py
│   └── db_manager.py      # InfluxDB connection and queries
├── components/            # UI components module
│   ├── __init__.py
│   └── visualizations.py # Charts and data visualization
├── utils/                 # Utility functions module
│   ├── __init__.py
│   └── helpers.py         # Helper functions and sidebar
├── styles/                # Styling module
│   ├── __init__.py
│   └── css.py            # CSS styles
└── users.json            # User data storage
```

## 🚀 Benefits of Modular Architecture

### **1. Separation of Concerns**

-   **Authentication**: User management, login/logout, permissions
-   **Database**: InfluxDB connections, data fetching, caching
-   **Components**: UI components, visualizations, charts
-   **Utils**: Helper functions, configuration, utilities
-   **Styles**: CSS styling separate from logic

### **2. Improved Maintainability**

-   Each module has a single responsibility
-   Easier to debug and test individual components
-   Changes in one module don't affect others
-   Clear interfaces between modules

### **3. Better Code Reusability**

-   Components can be easily reused across different parts
-   Shared utilities available to all modules
-   Consistent patterns and interfaces

### **4. Enhanced Scalability**

-   Easy to add new features without affecting existing code
-   Modules can be developed independently
-   Better team collaboration possibilities

### **5. Cleaner Code Organization**

-   Related functionality grouped together
-   Reduced code duplication
-   Clear import structure
-   Better documentation possibilities

## 🔧 Installation & Setup

### Prerequisites

-   Python 3.8+
-   Access to InfluxDB Cloud instance

### Installation Steps

1. **Install Dependencies:**

    ```bash
    pip install -r requirements-modular.txt
    ```

2. **Run the Modular Dashboard:**
    ```bash
    streamlit run dashboard_modular.py
    ```

## 📋 Module Details

### **Auth Module (`auth/`)**

-   `user_manager.py`: Core user management logic

    -   User authentication and authorization
    -   Password hashing and validation
    -   User CRUD operations
    -   Permission management

-   `auth_ui.py`: Authentication UI components
    -   Login form rendering
    -   User management interface
    -   Admin panel components

### **Database Module (`database/`)**

-   `db_manager.py`: Database operations
    -   InfluxDB client management
    -   Data fetching and caching
    -   Connection testing
    -   Data validation and cleaning

### **Components Module (`components/`)**

-   `visualizations.py`: UI and visualization components
    -   Chart creation (temperature, humidity, light)
    -   Status evaluation and alerts
    -   Data tables and metrics
    -   Permission-based data display

### **Utils Module (`utils/`)**

-   `helpers.py`: Utility functions
    -   Sensor calibration algorithms
    -   Sidebar controls rendering
    -   Footer and system info display
    -   Session state management

### **Styles Module (`styles/`)**

-   `css.py`: CSS styling
    -   Dashboard theme and colors
    -   Responsive design rules
    -   Animation definitions
    -   Status indicators styling

## 🔐 User Management

The modular architecture maintains all authentication features:

-   **Multi-user support** with role-based access
-   **Admin panel** for user management
-   **Permission system** for feature access control
-   **Secure password hashing** with salt
-   **Session management** with Streamlit

### Default Admin Access

-   **Username**: `admin`
-   **Password**: `cisco1234`

## 📊 Data Flow

1. **Authentication**: User login through `auth` module
2. **Permission Check**: Access control via `check_permission()`
3. **Data Fetching**: Database queries through `database` module
4. **Data Processing**: Validation and cleaning in database layer
5. **Visualization**: Chart creation through `components` module
6. **UI Rendering**: Interface elements via `utils` and `components`

## 🎨 Customization

### Adding New Features

1. **New Data Source**: Extend `DatabaseManager` class
2. **New Visualization**: Add functions to `visualizations.py`
3. **New UI Component**: Create in appropriate module
4. **New Permission**: Update `UserManager` class

### Configuration

-   **Database settings**: Modify `config.py`
-   **UI settings**: Update `UI_CONFIG` in `config.py`
-   **Sensor thresholds**: Adjust `SENSOR_THRESHOLDS`

## 🔄 Migration from Monolithic Version

The original `dashboard.py` remains functional. To migrate:

1. **Data Compatibility**: User data (`users.json`) is compatible
2. **Configuration**: Update any hardcoded values using `config.py`
3. **Dependencies**: Install from `requirements-modular.txt`
4. **Testing**: Run both versions side-by-side for comparison

## 🚀 Performance Benefits

-   **Faster imports**: Only load needed modules
-   **Better caching**: Module-level caching strategies
-   **Reduced memory**: Lazy loading of components
-   **Optimized queries**: Centralized database management

## 🧪 Testing

Each module can be tested independently:

```python
# Test authentication
from auth import UserManager
user_mgr = UserManager()

# Test database
from database import DatabaseManager
db_mgr = DatabaseManager()

# Test components
from components import create_environmental_chart
```

## 📈 Future Enhancements

The modular architecture enables:

-   **Plugin system** for custom sensors
-   **Theme system** for different UI styles
-   **API module** for external integrations
-   **Testing framework** for automated testing
-   **Logging module** for system monitoring
-   **Cache module** for advanced caching strategies

## 🎯 Best Practices

1. **Import only what you need** from each module
2. **Use type hints** for better code documentation
3. **Follow module interfaces** for consistency
4. **Keep modules loosely coupled**
5. **Document module functions** with docstrings

This modular architecture provides a solid foundation for scaling the Smart Campus Dashboard while maintaining the powerful features and user experience of the original application.
