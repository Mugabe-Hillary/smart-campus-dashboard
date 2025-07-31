"""
CSS styles for Smart Campus Dashboard
"""


def get_dashboard_styles():
    """Return CSS styles for the dashboard."""
    return """
<style>
    .main > div {
        padding-top: 2rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-good { border-left: 5px solid #28a745; }
    .status-warning { border-left: 5px solid #ffc107; }
    .status-danger { border-left: 5px solid #dc3545; }
    
    /* Data freshness indicators */
    .stale-data {
        opacity: 0.7;
        border: 2px dashed #ffc107;
        border-radius: 8px;
        padding: 0.5rem;
        background-color: rgba(255, 193, 7, 0.1);
    }
    
    .live-data {
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 0.5rem;
        background-color: rgba(40, 167, 69, 0.1);
    }
    
    /* Enhanced alerts */
    .status-banner {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: bold;
        text-align: center;
    }
    
    .status-success {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
    }
    
    .status-warning {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
        color: #212529;
    }
    
    .status-error {
        background: linear-gradient(90deg, #dc3545, #e83e8c);
        color: white;
    }
    
    @media (max-width: 768px) {
        .element-container {
            width: 100% !important;
        }
    }
    
    .stAlert > div {
        padding: 0.5rem;
    }
    
    /* Pulse animation for live data indicators */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .live-indicator {
        animation: pulse 2s infinite;
    }
</style>
"""
