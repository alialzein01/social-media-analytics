"""
Custom CSS Theme for Social Media Analytics Dashboard
======================================================

Design system: single source of truth for colors, typography, and chart styling.
- THEME_COLORS: primary, success, warning, info (buttons, status, alerts)
- SENTIMENT_COLORS: positive / negative / neutral (charts, word clouds)
- GRADIENT_STYLES: chart gradients
Use get_custom_css() for global styles; keep spacing/breakpoints consistent.
"""

# =============================================================================
# PROGRAMMATIC THEME TOKENS (use in Plotly, metric cards, etc.)
# Aligned with CSS variables in get_light_theme_css()
# =============================================================================

THEME_COLORS = {
    "primary": "#6366f1",
    "secondary": "#8b5cf6",
    "tertiary": "#475569",
    "background": "#f8fafc",
    "text": "#0f172a",
    "success": "#10b981",
    "warning": "#f59e0b",
    "info": "#3b82f6",
}

SENTIMENT_COLORS = {
    "positive": "#10b981",
    "negative": "#ef4444",
    "neutral": "#64748b",
}

GRADIENT_STYLES = {
    "purple": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "pink": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    "blue": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    "green": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
    "orange": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    "teal": "linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%)",
}


def get_custom_css(theme: str = "light") -> str:
    """
    Get custom CSS for the dashboard.

    Args:
        theme: 'light' or 'dark'

    Returns:
        CSS string
    """

    if theme == "dark":
        return get_dark_theme_css()
    else:
        return get_light_theme_css()


def get_light_theme_css() -> str:
    """Get light theme CSS."""
    return """
    <style>
        /* ============================================
           GLOBAL STYLES
           ============================================ */

        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* Root Variables - Light Theme */
        :root {
            /* Primary Colors */
            --primary-color: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #818cf8;

            /* Secondary Colors */
            --secondary-color: #8b5cf6;
            --secondary-dark: #7c3aed;
            --secondary-light: #a78bfa;

            /* Accent Colors */
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
            --accent-pink: #ec4899;

            /* Neutral Colors */
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border-color: #e2e8f0;
            --shadow-color: rgba(15, 23, 42, 0.1);

            /* Gradients */
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-success: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            --gradient-warning: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-info: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --gradient-purple: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-blue: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
            --gradient-green: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            --gradient-orange: linear-gradient(135deg, #fa709a 0%, #fee140 100%);

            /* Spacing */
            --spacing-xs: 0.25rem;
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 1.5rem;
            --spacing-xl: 2rem;
            --spacing-2xl: 3rem;

            /* Border Radius */
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            --radius-xl: 1rem;
            --radius-2xl: 1.5rem;

            /* Shadows */
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

            /* Transitions */
            --transition-fast: 150ms ease-in-out;
            --transition-base: 300ms ease-in-out;
            --transition-slow: 500ms ease-in-out;
        }

        /* ============================================
           STREAMLIT OVERRIDES
           ============================================ */

        /* Main Container */
        .main {
            background: var(--bg-secondary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-primary);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: var(--bg-primary);
            border-right: 1px solid var(--border-color);
            box-shadow: var(--shadow-md);
        }

        [data-testid="stSidebar"] > div:first-child {
            background: var(--bg-primary);
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.5rem;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: var(--spacing-lg);
        }

        h2 {
            font-size: 2rem;
            margin-top: var(--spacing-xl);
            margin-bottom: var(--spacing-md);
            color: var(--text-primary);
        }

        h3 {
            font-size: 1.5rem;
            margin-top: var(--spacing-lg);
            margin-bottom: var(--spacing-md);
            color: var(--text-primary);
        }

        /* ============================================
           CUSTOM COMPONENTS
           ============================================ */

        /* Metric Cards */
        [data-testid="stMetric"] {
            background: var(--bg-primary);
            padding: var(--spacing-lg);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            transition: all var(--transition-base);
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        [data-testid="stMetric"] label {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
        }

        /* UI module: page header and KPI cards */
        .ui-page-header { margin-bottom: 1.5rem; }
        .ui-kpi-card {
            transition: box-shadow var(--transition-base);
        }
        .ui-kpi-card:hover {
            box-shadow: var(--shadow-md);
        }
        .ui-section-gap { margin-top: 1.5rem; }

        /* Info/Warning/Success/Error Boxes */
        .stAlert {
            border-radius: var(--radius-md);
            border: none;
            padding: var(--spacing-md) var(--spacing-lg);
            font-weight: 500;
        }

        [data-baseweb="notification"] {
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-md);
        }

        /* Buttons */
        .stButton > button {
            background: var(--gradient-primary);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: var(--spacing-sm) var(--spacing-lg);
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all var(--transition-base);
            box-shadow: var(--shadow-md);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
            filter: brightness(1.1);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Select Boxes */
        [data-baseweb="select"] {
            border-radius: var(--radius-md);
            border: 2px solid var(--border-color);
            transition: all var(--transition-base);
        }

        [data-baseweb="select"]:hover {
            border-color: var(--primary-color);
        }

        /* Text Input */
        [data-baseweb="input"] {
            border-radius: var(--radius-md);
            border: 2px solid var(--border-color);
            transition: all var(--transition-base);
        }

        [data-baseweb="input"]:focus-within {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: var(--spacing-md);
            background: var(--bg-primary);
            padding: var(--spacing-sm);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: var(--radius-md);
            padding: var(--spacing-sm) var(--spacing-lg);
            font-weight: 600;
            color: var(--text-secondary);
            transition: all var(--transition-base);
        }

        .stTabs [aria-selected="true"] {
            background: var(--gradient-primary);
            color: white;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background: var(--bg-primary);
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            padding: var(--spacing-md);
            font-weight: 600;
            transition: all var(--transition-base);
        }

        .streamlit-expanderHeader:hover {
            background: var(--bg-tertiary);
            border-color: var(--primary-color);
        }

        /* DataFrame */
        [data-testid="stDataFrame"] {
            border-radius: var(--radius-md);
            overflow: hidden;
            box-shadow: var(--shadow-md);
        }

        /* Charts */
        [data-testid="stPlotlyChart"],
        [data-testid="stArrowVegaLiteChart"] {
            border-radius: var(--radius-lg);
            background: var(--bg-primary);
            padding: var(--spacing-md);
            box-shadow: var(--shadow-md);
        }

        /* ============================================
           CUSTOM CARD STYLES
           ============================================ */

        .metric-card {
            background: var(--bg-primary);
            border-radius: var(--radius-xl);
            padding: var(--spacing-xl);
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-color);
            transition: all var(--transition-base);
            height: 100%;
        }

        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl);
        }

        .metric-card-header {
            display: flex;
            align-items: center;
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-lg);
        }

        .metric-card-icon {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-lg);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }

        .metric-card-value {
            font-size: 2.5rem;
            font-weight: 800;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
        }

        .metric-card-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: var(--spacing-sm);
        }

        /* ============================================
           GRADIENT BACKGROUNDS
           ============================================ */

        .gradient-primary {
            background: var(--gradient-primary);
        }

        .gradient-success {
            background: var(--gradient-success);
        }

        .gradient-warning {
            background: var(--gradient-warning);
        }

        .gradient-info {
            background: var(--gradient-info);
        }

        .gradient-purple {
            background: var(--gradient-purple);
        }

        .gradient-blue {
            background: var(--gradient-blue);
        }

        .gradient-green {
            background: var(--gradient-green);
        }

        .gradient-orange {
            background: var(--gradient-orange);
        }

        /* ============================================
           LOADING STATES
           ============================================ */

        .loading-spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 4px solid var(--border-color);
            border-radius: 50%;
            border-top-color: var(--primary-color);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loading-dots {
            display: inline-flex;
            gap: var(--spacing-sm);
        }

        .loading-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary-color);
            animation: bounce 1.4s infinite ease-in-out both;
        }

        .loading-dot:nth-child(1) { animation-delay: -0.32s; }
        .loading-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        /* ============================================
           UTILITY CLASSES
           ============================================ */

        .text-center { text-align: center; }
        .text-left { text-align: left; }
        .text-right { text-align: right; }

        .font-bold { font-weight: 700; }
        .font-semibold { font-weight: 600; }
        .font-medium { font-weight: 500; }

        .text-primary { color: var(--text-primary); }
        .text-secondary { color: var(--text-secondary); }
        .text-muted { color: var(--text-muted); }

        .mb-1 { margin-bottom: var(--spacing-sm); }
        .mb-2 { margin-bottom: var(--spacing-md); }
        .mb-3 { margin-bottom: var(--spacing-lg); }
        .mb-4 { margin-bottom: var(--spacing-xl); }

        .mt-1 { margin-top: var(--spacing-sm); }
        .mt-2 { margin-top: var(--spacing-md); }
        .mt-3 { margin-top: var(--spacing-lg); }
        .mt-4 { margin-top: var(--spacing-xl); }

        /* ============================================
           RESPONSIVE
           ============================================ */

        @media (max-width: 768px) {
            h1 { font-size: 2rem; }
            h2 { font-size: 1.5rem; }
            h3 { font-size: 1.25rem; }

            .metric-card-value { font-size: 2rem; }
        }

        /* ============================================
           ANIMATIONS
           ============================================ */

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .fade-in {
            animation: fadeIn var(--transition-base);
        }

        .slide-in {
            animation: slideIn var(--transition-base);
        }

        /* ============================================
           SCROLLBAR STYLING
           ============================================ */

        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--text-muted);
            border-radius: var(--radius-md);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
    </style>
    """


def get_dark_theme_css() -> str:
    """Get dark theme CSS."""
    return """
    <style>
        /* ============================================
           DARK THEME
           ============================================ */

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {
            /* Primary Colors */
            --primary-color: #818cf8;
            --primary-dark: #6366f1;
            --primary-light: #a5b4fc;

            /* Background Colors */
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;

            /* Text Colors */
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;

            /* Border */
            --border-color: #334155;
            --shadow-color: rgba(0, 0, 0, 0.5);

            /* Gradients */
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-success: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            --gradient-warning: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-info: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }

        .main {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        [data-testid="stSidebar"] {
            background: var(--bg-primary);
            border-right: 1px solid var(--border-color);
        }

        [data-testid="stSidebar"] > div:first-child {
            background: var(--bg-primary);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary);
        }

        [data-testid="stMetric"] {
            background: var(--bg-tertiary);
            border-color: var(--border-color);
        }

        .metric-card {
            background: var(--bg-tertiary);
            border-color: var(--border-color);
        }

        .streamlit-expanderHeader {
            background: var(--bg-tertiary);
            border-color: var(--border-color);
        }

        [data-testid="stPlotlyChart"],
        [data-testid="stArrowVegaLiteChart"] {
            background: var(--bg-tertiary);
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--text-muted);
        }
    </style>
    """
