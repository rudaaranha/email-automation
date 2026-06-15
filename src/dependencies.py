"""
Dependency Injection module for FastAPI

This module provides factory functions that create and return singleton instances
of core application components. Using Depends() in the API endpoints ensures that
all requests share the same instances, preserving cache and configuration consistency.

Singleton Pattern Benefits:
    - Preserves cache beetween requests (researchers, activities)
    - Maintains consistent configuration across the application
    - Reduces memory usage (only one instance)
    - Makes testing easier (can mock dependencies)

Usage in API endpoints:
    @router.get("/status)
    async def get_status(alert_system = Depends(get_alert_system)):
        return alert_system.get_status()
"""

from src.config import Config
from src.alert_system import AlertSystem


# ===========================================
# SINGLETON CACHE VARIABLES
# ===========================================

# Private global variables to hold singleton instances
# The underscore prefix indicates these should not be accessed directly
_config_instance = None
_alert_system_instance = None


# ===========================================
# CONFIGURATION DEPENDENCY
# ===========================================

def get_config() -> Config:
    """
    Factory function that returns a singleton instance of Config

    The config class loads environment variables from .env file and provides access to all
    application settings including:
        - Email credentials (EMAIL_NATS, SENHA_APP_NATS)
        - Spreadsheet IDs (SPREADSHEET_ID_*)
        - Test mode flag

    Returns:
        Config: Singleton instance with loaded environment variables
    
    Example:
        config = get_config()
        print(config.EMAIL_NATS)
        print(config.TEST_MODE)
    
    Notes:
        - First call creates and caches the instance
        - Subsequent calls return the cached instance
        - Thread-safe for typical FastAPI usage (single thread per request)
    """
    global _config_instance

    if _config_instance is None:
        # Create new instance only once
        _config_instance = Config()
        print("Config instance created (singleton)")
    
    return _config_instance


# ===========================================
# ALERT SYSTEM DEPENDENCY
# ===========================================

def get_alert_system() -> AlertSystem:
    """
    Factory function that returns a singleton instance of AlertSystem

    The AlertSystem is the core orchestrator of the application. It:
        - Uses SpreadsheetManager to read Google Sheets
        - Uses EmailDispatcher to send alerts
        - Manages cache for researchers and activities
        - Processes all configured spreadsheet

    Return:
        AlertSystem: Singleton instance ready to process alerts

    Example:
        alert_system = get_alert_system()
        result = alert_system.process_all_spreadsheet()
        print(f"Sent {result['alerts_sent']['start']} start alerts")
    
    Dependencies:
        - Uses get_config() to obtain application configuration
        - Config must be initialized before AlertSystem

    Notes:
        - First call creates AlertSystem with the current Config
        - Subsequent calls return the same instance (preserves cache)
        - The singleton ensures cache is shared across API requests
    """
    global _alert_system_instance

    if _alert_system_instance is None:
        # Get the singleton Config instance
        config = get_config()

        # Create AlertSystem with the config
        _alert_system_instance = AlertSystem(config)
        print("AlertSystem instance created (singleton)")
    
    return _alert_system_instance


# ============================================
# RESET FUNCTIONS FOR TESTING
# ============================================

def reset_singletons():
    """
    Reset singleton instances (FOR TESTING ONLY).
    
    This function should only be used in unit tests to ensure
    isolation between test cases. It resets both the Config and
    AlertSystem singletons so the next call to get_config() or
    get_alert_system() creates fresh instances.
    
    WARNING: Do not use this in production code!
    
    Example (in tests):
        from src.dependencies import reset_singletons
        
        def test_something():
            reset_singletons()  # Fresh state for this test
            config = get_config()
            # ... test code ...
    
    Notes:
        - Only import and call this in test files
        - Not exposed in the main __init__.py to prevent accidental use
    """
    global _config_instance, _alert_system_instance
    
    _config_instance = None
    _alert_system_instance = None
    
    print("Singleton instances reset (testing only)")


# ============================================
# HELPER FUNCTIONS (OPTIONAL)
# ============================================

def is_ready() -> bool:
    """
    Check if all dependencies are initialized.
    
    Returns:
        bool: True if AlertSystem is ready, False otherwise
    
    Example:
        if is_ready():
            alert_system = get_alert_system()
        else:
            print("System not ready")
    """
    return _alert_system_instance is not None


def get_system_status() -> dict:
    """
    Get current status of dependency system.
    
    Returns:
        dict: Status information including:
            - config_initialized: Whether Config is ready
            - alert_system_initialized: Whether AlertSystem is ready
            - test_mode: Current test mode setting (if config exists)
    
    Example:
        status = get_system_status()
        print(f"AlertSystem ready: {status['alert_system_initialized']}")
    """
    status = {
        "config_initialized": _config_instance is not None,
        "alert_system_initialized": _alert_system_instance is not None,
    }
    
    # Add test mode info if config exists
    if _config_instance:
        status["test_mode"] = _config_instance.TEST_MODE
    
    return status
