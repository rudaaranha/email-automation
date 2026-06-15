"""
Unit tests for dependencies.py

Tests verify:
- Singleton pattern works correctly (same instance returned)
- Reset function properly clears instances
- AlertSystem uses the same Config instance
- Helper functions return correct status information
"""

import pytest
from src.dependencies import (
    get_config,
    get_alert_system,
    reset_singletons,
    is_ready,
    get_system_status
)


class TestDependencies:
    """Test suite for dependency injection module"""
    
    def setup_method(self):
        """Reset singletons before each test to ensure clean state"""
        reset_singletons()
    
    def teardown_method(self):
        """Reset singletons after each test to avoid affecting other tests"""
        reset_singletons()
    
    # ============================================
    # TESTS FOR get_config
    # ============================================
    
    def test_get_config_singleton(self):
        """Test that get_config always returns the same instance"""
        config1 = get_config()
        config2 = get_config()
        config3 = get_config()
        
        # All should be the same object
        assert config1 is config2
        assert config2 is config3
        assert config1 is config3
    
    def test_get_config_returns_config_instance(self):
        """Test that get_config returns a valid Config object"""
        config = get_config()
        
        # Should have expected attributes
        assert hasattr(config, 'EMAIL_NATS')
        assert hasattr(config, 'SENHA_APP_NATS')
        assert hasattr(config, 'SPREADSHEETS')
        assert hasattr(config, 'TEST_MODE')
    
    def test_config_loaded_from_environment(self):
        """Test that Config loads environment variables correctly"""
        config = get_config()
        
        # These should be set from .env or environment
        # Note: In test environment, these are set in conftest.py
        assert config.EMAIL_NATS is not None or config.TEST_MODE is True
    
    # ============================================
    # TESTS FOR get_alert_system
    # ============================================
    
    def test_get_alert_system_singleton(self):
        """Test that get_alert_system always returns the same instance"""
        system1 = get_alert_system()
        system2 = get_alert_system()
        system3 = get_alert_system()
        
        # All should be the same object
        assert system1 is system2
        assert system2 is system3
        assert system1 is system3
    
    def test_get_alert_system_returns_alert_system_instance(self):
        """Test that get_alert_system returns a valid AlertSystem object"""
        system = get_alert_system()
        
        # Should have expected attributes/methods
        assert hasattr(system, 'process_all_spreadsheets')
        assert hasattr(system, 'process_single_project')
        assert hasattr(system, 'spreadsheet_manager')
        assert hasattr(system, 'email_dispatcher')
    
    def test_alert_system_uses_same_config_as_get_config(self):
        """Test that AlertSystem uses the same Config instance as get_config"""
        config = get_config()
        alert_system = get_alert_system()
        
        # AlertSystem's config should be the same object
        assert alert_system.config is config
    
    # ============================================
    # TESTS FOR reset_singletons
    # ============================================
    
    def test_reset_singletons_clears_config(self):
        """Test that reset_singletons creates new Config instances"""
        config1 = get_config()
        reset_singletons()
        config2 = get_config()
        
        # Should be different instances
        assert config1 is not config2
    
    def test_reset_singletons_clears_alert_system(self):
        """Test that reset_singletons creates new AlertSystem instances"""
        system1 = get_alert_system()
        reset_singletons()
        system2 = get_alert_system()
        
        # Should be different instances
        assert system1 is not system2
    
    def test_reset_singletons_multiple_calls(self):
        """Test that calling reset_singletons multiple times works"""
        config1 = get_config()
        reset_singletons()
        reset_singletons()  # Second call should do nothing harmful
        config2 = get_config()
        
        assert config1 is not config2
    
    # ============================================
    # TESTS FOR is_ready
    # ============================================
    
    def test_is_ready_false_before_initialization(self):
        """Test that is_ready returns False before any initialization"""
        # Ensure clean state
        reset_singletons()
        
        assert is_ready() is False
    
    def test_is_ready_true_after_alert_system_initialized(self):
        """Test that is_ready returns True after AlertSystem is created"""
        reset_singletons()
        assert is_ready() is False
        
        # Initialize AlertSystem
        get_alert_system()
        
        assert is_ready() is True
    
    def test_is_ready_config_only_not_enough(self):
        """Test that is_ready only returns True when AlertSystem is ready"""
        reset_singletons()
        
        # Only Config initialized
        get_config()
        
        # is_ready should still be False (AlertSystem not ready)
        assert is_ready() is False
        
        # Now initialize AlertSystem
        get_alert_system()
        assert is_ready() is True
    
    # ============================================
    # TESTS FOR get_system_status
    # ============================================
    
    def test_get_system_status_before_initialization(self):
        """Test status before any initialization"""
        reset_singletons()
        
        status = get_system_status()
        
        assert status["config_initialized"] is False
        assert status["alert_system_initialized"] is False
        assert "test_mode" not in status
    
    def test_get_system_status_after_config_only(self):
        """Test status after only Config is initialized"""
        reset_singletons()
        get_config()
        
        status = get_system_status()
        
        assert status["config_initialized"] is True
        assert status["alert_system_initialized"] is False
        assert "test_mode" in status  # Config provides test_mode
    
    def test_get_system_status_after_full_initialization(self):
        """Test status after full initialization"""
        reset_singletons()
        get_alert_system()
        
        status = get_system_status()
        
        assert status["config_initialized"] is True
        assert status["alert_system_initialized"] is True
        assert "test_mode" in status
    
    def test_get_system_status_returns_test_mode_value(self):
        """Test that test_mode value is correctly reported"""
        reset_singletons()
        
        # Get config and check test_mode
        config = get_config()
        expected_test_mode = config.TEST_MODE
        
        status = get_system_status()
        
        assert status["test_mode"] == expected_test_mode
    
    # ============================================
    # TESTS FOR ISOLATION BETWEEN TESTS
    # ============================================
    
    def test_isolation_between_tests_with_reset(self):
        """Test that reset ensures tests don't interfere with each other"""
        # This test should not affect others because of teardown
        config_before = get_config()
        
        # Store something in config (if mutable)
        # Not needed - just checking that reset works
        
        reset_singletons()
        config_after = get_config()
        
        assert config_before is not config_after
    
    def test_multiple_alert_system_calls_same_instance(self):
        """Test that multiple calls to get_alert_system return same instance"""
        reset_singletons()
        
        system1 = get_alert_system()
        system2 = get_alert_system()
        system3 = get_alert_system()
        
        assert system1 is system2
        assert system2 is system3
    
    def test_get_alert_system_after_reset_creates_new(self):
        """Test that after reset, a new AlertSystem is created"""
        reset_singletons()
        system1 = get_alert_system()
        
        reset_singletons()
        system2 = get_alert_system()
        
        assert system1 is not system2


class TestDependenciesConcurrency:
    """Test concurrent access to singletons (conceptual)"""
    
    def test_singleton_thread_safety_concept(self):
        """
        Conceptual test for singleton behavior.
        
        FastAPI typically runs in a single-threaded async model,
        so true concurrency tests are less critical. This test
        verifies the singleton pattern works correctly.
        """
        reset_singletons()
        
        config1 = get_config()
        config2 = get_config()
        
        # Verify singleton property
        assert config1 is config2
