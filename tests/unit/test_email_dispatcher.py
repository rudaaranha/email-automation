"""
Unit tests for email_dispatcher.py

Tests verify:
- Test mode works correctly (doesn't send real emails)
- Production mode sends emails via SMTP
- Authentication and SMTP errors are handled
- Each alert method calls the correct template
"""

import pytest
from unittest.mock import Mock, patch, ANY
from src.email_dispatcher import EmailDispatcher
from src.config import Config


class TestEmailDispatcher:
    """Test suite for EmailDispatcher class"""
    
    def setup_method(self):
        """Setup before each test"""
        self.config = Config()
        self.dispatcher = EmailDispatcher(self.config)
    
    def test_send_email_test_mode(self):
        """Test that _send doesn't actually connect to SMTP in test mode"""
        # Set test mode
        self.config.TEST_MODE = True
        dispatcher = EmailDispatcher(self.config)
        
        # Mock SMTP to detect if it's called
        with patch('smtplib.SMTP') as mock_smtp:
            result = dispatcher._send(
                to_email="teste@example.com",
                subject="Test Subject",
                html_body="<html><body>Test</body></html>"
            )
            
            # SMTP should NOT be called in test mode
            mock_smtp.assert_not_called()
            
            # Result should be True (simulated success)
            assert result is True
    
    def test_send_email_production_success(self):
        """Test that _send successfully connects to SMTP in production mode"""
        # Ensure test mode is off
        self.config.TEST_MODE = False
        dispatcher = EmailDispatcher(self.config)
        
        # Mock SMTP
        with patch('smtplib.SMTP') as mock_smtp_class:
            # Create mock server instance
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            
            result = dispatcher._send(
                to_email="teste@example.com",
                subject="Test Subject",
                html_body="<html><body>Test</body></html>"
            )
            
            # Verify SMTP was called correctly
            mock_smtp_class.assert_called_once_with(
                dispatcher.smtp_server, 
                dispatcher.smtp_port
            )
            
            # Verify starttls, login, and send_message were called
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with(
                dispatcher.email, 
                dispatcher.password
            )
            mock_server.send_message.assert_called_once()
            
            assert result is True
    
    def test_send_email_authentication_error(self):
        """Test that authentication errors are handled gracefully"""
        self.config.TEST_MODE = False
        dispatcher = EmailDispatcher(self.config)
        
        # Mock SMTP to raise authentication error
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
            
            result = dispatcher._send(
                to_email="teste@example.com",
                subject="Test",
                html_body="<html></html>"
            )
            
            assert result is False
    
    def test_send_email_smtp_error(self):
        """Test that general SMTP errors are handled gracefully"""
        self.config.TEST_MODE = False
        dispatcher = EmailDispatcher(self.config)
        
        # Mock SMTP to raise general SMTP error
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = smtplib.SMTPException("Connection failed")
            
            result = dispatcher._send(
                to_email="teste@example.com",
                subject="Test",
                html_body="<html></html>"
            )
            
            assert result is False
    
    def test_send_alert_start_calls_correct_template(self):
        """Test that send_alert_start calls alert_start template with correct params"""
        # Mock _send to avoid actual email sending
        self.dispatcher._send = Mock(return_value=True)
        
        # Mock the templates
        self.dispatcher.templates.alert_start = Mock(return_value="<html>Mocked HTML</html>")
        
        result = self.dispatcher.send_alert_start(
            to_email="joao@lab.com",
            responsible_name="João Silva",
            activity_name="Revisão de documento",
            start_date="01/04/2026",
            end_date="10/04/2026",
            project_name="Sensor Diabetes"
        )
        
        # Verify template was called with correct parameters
        self.dispatcher.templates.alert_start.assert_called_once_with(
            responsible_name="João Silva",
            activity_name="Revisão de documento",
            start_date="01/04/2026",
            end_date="10/04/2026",
            project_name="Sensor Diabetes"
        )
        
        # Verify _send was called with correct parameters
        self.dispatcher._send.assert_called_once()
        call_args = self.dispatcher._send.call_args[0]
        assert call_args[0] == "joao@lab.com"  # to_email
        assert "[ALERT] Start Activity: Revisão de documento - Sensor Diabetes" in call_args[1]  # subject
        assert call_args[2] == "<html>Mocked HTML</html>"  # html_body
        
        assert result is True
    
    def test_send_alert_delay_calls_correct_template(self):
        """Test that send_alert_delay calls alert_delay template with correct params"""
        self.dispatcher._send = Mock(return_value=True)
        self.dispatcher.templates.alert_delay = Mock(return_value="<html>Mocked HTML</html>")
        
        result = self.dispatcher.send_alert_delay(
            to_email="maria@lab.com",
            responsible_name="Maria Silva",
            activity_name="Extração de dados",
            end_date="05/04/2026",
            days_delayed=5,
            project_name="Sensor Diabetes"
        )
        
        self.dispatcher.templates.alert_delay.assert_called_once_with(
            responsible_name="Maria Silva",
            activity_name="Extração de dados",
            end_date="05/04/2026",
            days_delayed=5,
            project_name="Sensor Diabetes"
        )
        
        self.dispatcher._send.assert_called_once()
        call_args = self.dispatcher._send.call_args[0]
        assert "[URGENT] Delayed Activity: Extração de dados - Sensor Diabetes" in call_args[1]
        
        assert result is True
    
    def test_send_alert_completion_calls_correct_template(self):
        """Test that send_alert_completion calls alert_completion template with correct params"""
        self.dispatcher._send = Mock(return_value=True)
        self.dispatcher.templates.alert_completion = Mock(return_value="<html>Mocked HTML</html>")
        
        result = self.dispatcher.send_alert_completion(
            to_email="pedro@lab.com",
            responsible_name="Pedro Souza",
            activity_name="Reunião inicial",
            project_name="Sensor Diabetes"
        )
        
        self.dispatcher.templates.alert_completion.assert_called_once_with(
            responsible_name="Pedro Souza",
            activity_name="Reunião inicial",
            project_name="Sensor Diabetes"
        )
        
        assert result is True
    
    def test_send_daily_report_calls_correct_template(self):
        """Test that send_daily_report calls daily_report template with correct params"""
        self.dispatcher._send = Mock(return_value=True)
        self.dispatcher.templates.daily_report = Mock(return_value="<html>Mocked HTML</html>")
        
        activities_to_start = [{"atividade": "Tarefa A", "data_fim": "10/04/2026"}]
        activities_delayed = [{"atividade": "Tarefa B", "dias_atraso": 3}]
        
        result = self.dispatcher.send_daily_report(
            to_email="coordenador@lab.com",
            activities_to_start=activities_to_start,
            activities_delayed=activities_delayed,
            project_name="Sensor Diabetes"
        )
        
        self.dispatcher.templates.daily_report.assert_called_once_with(
            activities_to_start=activities_to_start,
            activities_delayed=activities_delayed,
            project_name="Sensor Diabetes"
        )
        
        assert result is True
    
    def test_alert_start_subject_format(self):
        """Test that alert_start generates correct email subject"""
        self.dispatcher._send = Mock(return_value=True)
        self.dispatcher.templates.alert_start = Mock(return_value="<html></html>")
        
        self.dispatcher.send_alert_start(
            to_email="teste@lab.com",
            responsible_name="João",
            activity_name="Minha Atividade",
            start_date="01/04/2026",
            end_date="10/04/2026",
            project_name="Projeto X"
        )
        
        call_args = self.dispatcher._send.call_args[0]
        subject = call_args[1]
        
        assert "ALERT" in subject
        assert "Start Activity" in subject
        assert "Minha Atividade" in subject
        assert "Projeto X" in subject
    
    def test_alert_delay_subject_format(self):
        """Test that alert_delay generates correct email subject"""
        self.dispatcher._send = Mock(return_value=True)
        self.dispatcher.templates.alert_delay = Mock(return_value="<html></html>")
        
        self.dispatcher.send_alert_delay(
            to_email="teste@lab.com",
            responsible_name="João",
            activity_name="Minha Atividade",
            end_date="10/04/2026",
            days_delayed=3,
            project_name="Projeto X"
        )
        
        call_args = self.dispatcher._send.call_args[0]
        subject = call_args[1]
        
        assert "URGENT" in subject
        assert "Delayed Activity" in subject
        assert "Minha Atividade" in subject
        assert "Projeto X" in subject


# Import smtplib for exception types (needed for the test)
import smtplib