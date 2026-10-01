"""
Unit tests for alert_system.py

Tests verify:
- Processing of all spreadsheets configured
- Correct detection of start/delay/completion alerts
- Handling of multiple responsibilities
- Error handling and edge cases
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
from src.alert_system import AlertSystem
from src.config import Config
from src.models import AlertHistory, AlertType, ProjectState


class TestAlertSystem:
    """Test suite for AlertSystem class"""
    
    def setup_method(self):
        """Setup before each test"""

        self.config = Config()

        self.system_repository = Mock()
        self.system_repository.alert_was_sent.return_value = False

        self.alert_system = AlertSystem(
            self.config,
            system_repository=self.system_repository,
        )

        self.alert_system.email_dispatcher = Mock()
    
    def test_process_all_spreadsheets_calls_all_projects(self):
        """Test that process_all_spreadsheets processes each configured project"""
        # Mock the config to have multiple projects
        self.config.SPREADSHEETS = {
            "projeto1": "id_123",
            "projeto2": "id_456"
        }
        
        # Mock the _process_single_spreadsheet method
        self.alert_system._process_single_spreadsheet = Mock()
        
        result = self.alert_system.process_all_spreadsheets()
        
        # Should have been called twice (once per project)
        assert self.alert_system._process_single_spreadsheet.call_count == 2
        
        # Check call arguments
        calls = self.alert_system._process_single_spreadsheet.call_args_list
        assert calls[0][0][0] == "id_123"  # first call spreadsheet_id
        assert calls[0][0][1] == "projeto1"  # first call project_name
        assert calls[1][0][0] == "id_456"  # second call spreadsheet_id
        assert calls[1][0][1] == "projeto2"  # second call project_name
        
        # Check result structure
        assert "total_spreadsheets" in result
        assert "total_activities" in result
        assert "alerts_sent" in result
    
    def test_process_single_spreadsheet_loads_researchers_and_activities(self):
        """Test that _process_single_spreadsheet loads researchers and activities"""
        # Mock the spreadsheet_manager methods
        mock_researchers = {"JOÃO": "joao@email.com", "MARIA": "maria@email.com"}
        mock_activities = [{"atividade": "Teste", "status": "Não iniciada"}]
        
        self.alert_system.spreadsheet_manager.load_researchers = Mock(return_value=mock_researchers)
        self.alert_system.spreadsheet_manager.load_activities = Mock(return_value=mock_activities)
        
        # Mock _process_activity to avoid processing
        self.alert_system._process_activity = Mock()
        
        # Execute
        self.alert_system._process_single_spreadsheet("id_teste", "projeto_teste")
        
        # Verify
        self.alert_system.spreadsheet_manager.load_researchers.assert_called_once_with("id_teste")
        self.alert_system.spreadsheet_manager.load_activities.assert_called_once_with("id_teste")
    
    def test_process_single_spreadsheet_handles_load_researchers_error(self):
        """Test that error loading researchers is handled gracefully"""

        # Mock load_researchers to raise exception
        self.alert_system.spreadsheet_manager.load_researchers = Mock(
            side_effect=Exception("Connection failed")
        )
        self.alert_system.spreadsheet_manager.load_activities = Mock()
        
        # Execute (should not crash)
        self.alert_system._process_single_spreadsheet("id_teste", "projeto_teste")
        
        # load_activities should NOT be called if load_researchers fails
        self.alert_system.spreadsheet_manager.load_activities.assert_not_called()
        
        # Error should be recorded in stats
        assert len(self.alert_system.stats["errors"]) == 1
        assert "Connection failed" in self.alert_system.stats["errors"][0]
    
    def test_process_activity_start_alert(self):
        """Test that activity with start_date = today sends start alert"""
        today = date(2026, 4, 10)
        
        activity = {
            "atividade": "Revisão de documento",
            "status": "Não iniciada",
            "data_inicio": today,
            "data_fim": date(2026, 4, 20),
            "responsavel_raw": "JOÃO"
        }
        
        researchers = {"JOÃO": "joao@email.com"}
        
        # Mock the alert sending methods
        self.alert_system._send_start_alerts = Mock()
        self.alert_system._send_delay_alerts = Mock()
        self.alert_system._send_completion_alerts = Mock()
        
        # Execute
        self.alert_system._process_activity(activity, researchers, "projeto_teste", today)
        
        # Should call send_start_alerts, not others
        self.alert_system._send_start_alerts.assert_called_once()
        self.alert_system._send_delay_alerts.assert_not_called()
        self.alert_system._send_completion_alerts.assert_not_called()
    
    def test_process_activity_delay_alert(self):
        """Test that activity with end_date < today sends delay alert"""
        today = date(2026, 4, 10)
        
        activity = {
            "atividade": "Extração de dados",
            "status": "Não iniciada",
            "data_inicio": date(2026, 4, 1),
            "data_fim": date(2026, 4, 5),  # 5 days before today
            "responsavel_raw": "MARIA"
        }
        
        researchers = {"MARIA": "maria@email.com"}
        
        self.alert_system._send_start_alerts = Mock()
        self.alert_system._send_delay_alerts = Mock()
        self.alert_system._send_completion_alerts = Mock()
        
        self.alert_system._process_activity(activity, researchers, "projeto_teste", today)
        
        # Should call send_delay_alerts, not others
        self.alert_system._send_delay_alerts.assert_called_once()
        self.alert_system._send_start_alerts.assert_not_called()
        self.alert_system._send_completion_alerts.assert_not_called()
    
    def test_process_activity_completion_alert(self):
        """Test that completed activity sends completion alert"""
        today = date(2026, 4, 10)
        
        activity = {
            "atividade": "Reunião inicial",
            "status": "Concluída",
            "data_inicio": date(2026, 4, 2),
            "data_fim": date(2026, 4, 2),
            "responsavel_raw": "PEDRO"
        }
        
        researchers = {"PEDRO": "pedro@email.com"}
        
        self.alert_system._send_start_alerts = Mock()
        self.alert_system._send_delay_alerts = Mock()
        self.alert_system._send_completion_alerts = Mock()
        
        self.alert_system._process_activity(activity, researchers, "projeto_teste", today)
        
        # Should call send_completion_alerts, not others
        self.alert_system._send_completion_alerts.assert_called_once()
        self.alert_system._send_start_alerts.assert_not_called()
        self.alert_system._send_delay_alerts.assert_not_called()
    
    def test_process_activity_multiple_responsibilities(self):
        """Test that activity with multiple responsibilities sends alerts to all"""
        today = date(2026, 4, 10)
        
        activity = {
            "atividade": "Seleção pareada",
            "status": "Não iniciada",
            "data_inicio": today,
            "data_fim": date(2026, 4, 20),
            "responsavel_raw": "ALDENORA\nANA CAROLINA\nBÁRBARA"
        }
        
        researchers = {
            "ALDENORA": "aldenora@email.com",
            "ANA CAROLINA": "anacarolina@email.com",
            "BÁRBARA": "barbara@email.com"
        }
        
        self.alert_system._send_start_alerts = Mock()
        
        self.alert_system._process_activity(activity, researchers, "projeto_teste", today)
        
        # Should call _send_start_alerts with all 3 recipients
        self.alert_system._send_start_alerts.assert_called_once()
        call_args = self.alert_system._send_start_alerts.call_args[0][0]  # recipients
        assert len(call_args) == 3
        assert ("ALDENORA", "aldenora@email.com") in call_args
        assert ("ANA CAROLINA", "anacarolina@email.com") in call_args
        assert ("BÁRBARA", "barbara@email.com") in call_args
    
    def test_process_activity_skip_missing_email(self):
        """Test that activity skips responsibilities without email"""
        today = date(2026, 4, 10)
        
        activity = {
            "atividade": "Atividade teste",
            "status": "Não iniciada",
            "data_inicio": today,
            "data_fim": date(2026, 4, 20),
            "responsavel_raw": "JOÃO\nMARIA"
        }
        
        # Only JOÃO has email, MARIA doesn't
        researchers = {"JOÃO": "joao@email.com"}
        
        self.alert_system._send_start_alerts = Mock()
        
        self.alert_system._process_activity(activity, researchers, "projeto_teste", today)
        
        # Should call _send_start_alerts with only JOÃO
        self.alert_system._send_start_alerts.assert_called_once()
        call_args = self.alert_system._send_start_alerts.call_args[0][0]  # recipients
        assert len(call_args) == 1
        assert call_args[0][0] == "JOÃO"
    
    def test_process_activity_skip_without_responsible(self):
        """Test that activity without responsible is skipped"""
        today = date(2026, 4, 10)
        
        activity = {
            "atividade": "Atividade sem responsável",
            "status": "Não iniciada",
            "data_inicio": today,
            "data_fim": date(2026, 4, 20),
            "responsavel_raw": ""
        }
        
        researchers = {"JOÃO": "joao@email.com"}
        
        self.alert_system._send_start_alerts = Mock()
        
        self.alert_system._process_activity(activity, researchers, "projeto_teste", today)
        
        # No alerts should be sent
        self.alert_system._send_start_alerts.assert_not_called()
    
    def test_send_start_alerts(self):
        """Test that send_start_alerts sends emails to all recipients"""
        recipients = [
            ("JOÃO", "joao@email.com"),
            ("MARIA", "maria@email.com")
        ]
        
        # Mock email_dispatcher
        self.alert_system.email_dispatcher.send_alert_start = Mock(return_value=True)
        
        self.alert_system._send_start_alerts(
            recipients=recipients,
            activity_name="Teste Atividade",
            start_date="01/04/2026",
            end_date="10/04/2026",
            project_name="Projeto Teste"
        )
        
        # Should have been called twice
        assert self.alert_system.email_dispatcher.send_alert_start.call_count == 2
        
        # Check stats
        assert self.alert_system.stats["alerts_start"] == 2
    
    def test_send_start_alerts_with_failure(self):
        """Test that send_start_alerts handles email sending failures"""
        recipients = [("JOÃO", "joao@email.com")]
        
        # Mock email_dispatcher to return False (failure)
        self.alert_system.email_dispatcher.send_alert_start = Mock(return_value=False)
        
        self.alert_system._send_start_alerts(
            recipients=recipients,
            activity_name="Teste Atividade",
            start_date="01/04/2026",
            end_date="10/04/2026",
            project_name="Projeto Teste"
        )
        
        # Stats should not increment
        assert self.alert_system.stats["alerts_start"] == 0
        
        # Error should be recorded
        assert len(self.alert_system.stats["errors"]) == 1
        assert "Failed to send start alert" in self.alert_system.stats["errors"][0]
    
    def test_send_delay_alerts(self):
        """Test that send_delay_alerts sends emails to all recipients"""
        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        reference_date = date(2026, 10, 1)

        self.alert_system.email_dispatcher.send_alert_delay.return_value = True
        self.system_repository.alert_was_sent.return_value = False
        
        self.alert_system._send_delay_alerts(
            recipients=recipients,
            activity_name="Atividade Teste",
            end_date="30/09/2026",
            days_delayed=1,
            project_name="Projeto Teste",
            reference_date=reference_date,
        )

        # Verifica que o repositório foi consultado
        self.system_repository.alert_was_sent.assert_called_once_with(
            project="Projeto Teste",
            activity="Atividade Teste",
            researcher="JOÃO",
            alert_type=AlertType.ATRASO,
            reference_date=reference_date,
        )

        # Verifica que o e-mail foi enviado
        self.alert_system.email_dispatcher.send_alert_delay.assert_called_once()

        # Verifica que o histórico foi salvo
        self.system_repository.save_alert_history.assert_called_once()

        # Verifica a estatística
        assert self.alert_system.stats["alerts_delay"] == 1
        
    
    def test_send_completion_alerts(self):
        """Test that send_completion_alerts sends emails to all recipients"""
        recipients = [("MARIA", "maria@email.com")]
        
        self.alert_system.email_dispatcher.send_alert_completion = Mock(return_value=True)
        
        self.alert_system._send_completion_alerts(
            recipients=recipients,
            activity_name="Teste Atividade",
            project_name="Projeto Teste"
        )
        
        self.alert_system.email_dispatcher.send_alert_completion.assert_called_once()
        assert self.alert_system.stats["alerts_completion"] == 1
    
    def test_process_single_project_by_name(self):
        """Test that process_single_project processes a specific project by name"""
        self.config.SPREADSHEETS = {
            "sensor_diabetes": "id_123",
            "outro_projeto": "id_456"
        }
        
        # Mock _process_single_spreadsheet
        self.alert_system._process_single_spreadsheet = Mock()
        
        result = self.alert_system.process_single_project("sensor_diabetes")
        
        # Should have been called once with correct ID
        self.alert_system._process_single_spreadsheet.assert_called_once_with("id_123", "sensor_diabetes")
        
        assert result["project"] == "sensor_diabetes"
    
    def test_process_single_project_not_found(self):
        """Test that process_single_project returns error for unknown project"""
        self.config.SPREADSHEETS = {"projeto1": "id_123"}
        
        result = self.alert_system.process_single_project("projeto_inexistente")
        
        assert "error" in result
        assert "not found" in result["error"]
    
    def test_stats_reset_between_executions(self):
        """Test that statistics are reset between process executions"""
        self.config.SPREADSHEETS = {"projeto1": "id_123"}
        
        # Mock methods
        self.alert_system._process_single_spreadsheet = Mock()
        
        # First execution
        self.alert_system.process_all_spreadsheets()
        self.alert_system.stats["alerts_start"] = 5
        
        # Second execution should reset stats
        self.alert_system.process_all_spreadsheets()
        assert self.alert_system.stats["alerts_start"] == 0
        assert self.alert_system.stats["alerts_delay"] == 0
        assert self.alert_system.stats["alerts_completion"] == 0
        assert len(self.alert_system.stats["errors"]) == 0

    def test_new_project_is_registered_as_active(self):
        self.config.SPREADSHEETS = {
            "projeto_novo": "id_123"
        }

        self.system_repository.get_project_state.return_value = None
        self.alert_system._process_single_spreadsheet = Mock()

        self.alert_system.process_all_spreadsheets()

        self.system_repository.save_project_state.assert_called_once()

        saved_state = (
            self.system_repository.save_project_state.call_args[0][0]
        )

        assert saved_state.project == "projeto_novo"
        assert saved_state.spreadsheet_id == "id_123"
        assert saved_state.active is True

        self.alert_system._process_single_spreadsheet.assert_called_once_with(
            "id_123",
            "projeto_novo",
        )


    def test_inactive_project_is_not_processed(self):
        self.config.SPREADSHEETS = {
            "projeto_inativo": "id_123"
        }

        self.system_repository.get_project_state.return_value = ProjectState(
            project="projeto_inativo",
            spreadsheet_id="id_123",
            active=False,
        )

        self.alert_system._process_single_spreadsheet = Mock()

        result = self.alert_system.process_all_spreadsheets()

        self.alert_system._process_single_spreadsheet.assert_not_called()

        assert result["total_spreadsheets"] == 0


    def test_active_project_is_processed(self):
        self.config.SPREADSHEETS = {
            "projeto_ativo": "id_123"
        }

        self.system_repository.get_project_state.return_value = ProjectState(
            project="projeto_ativo",
            spreadsheet_id="id_123",
            active=True,
        )

        self.alert_system._process_single_spreadsheet = Mock()

        self.alert_system.process_all_spreadsheets()

        self.alert_system._process_single_spreadsheet.assert_called_once_with(
            "id_123",
            "projeto_ativo",
        )

        assert self.alert_system.stats["total_spreadsheets"] == 1

    def test_control_worksheets_are_ensured_before_processing(self):
        self.config.SPREADSHEETS = {
            "projeto1": "id_123"
        }

        self.system_repository.get_project_state.return_value = ProjectState(
            project="projeto1",
            spreadsheet_id="id_123",
            active=True,
        )

        self.alert_system._process_single_spreadsheet = Mock()

        self.alert_system.process_all_spreadsheets()

        self.system_repository.ensure_control_worksheets.assert_called_once()

    def test_completion_alert_is_saved_to_history(self):
        recipients = [
            ("MARIA", "maria@email.com")
        ]

        self.alert_system.email_dispatcher.send_alert_completion = Mock(
            return_value=True
        )

        self.alert_system._send_completion_alerts(
            recipients=recipients,
            activity_name="Atividade concluída",
            project_name="Projeto Teste",
        )

        self.system_repository.alert_was_sent.assert_called_once_with(
            project="Projeto Teste",
            activity="Atividade concluída",
            researcher="MARIA",
            alert_type=AlertType.CONCLUSAO,
        )

        self.system_repository.save_alert_history.assert_called_once()

        history = (
            self.system_repository.save_alert_history.call_args[0][0]
        )

        assert history.project == "Projeto Teste"
        assert history.activity == "Atividade concluída"
        assert history.researcher == "MARIA"
        assert history.email == "maria@email.com"
        assert history.alert_type == AlertType.CONCLUSAO

        assert self.alert_system.stats["alerts_completion"] == 1

    def test_completion_alert_is_not_sent_if_already_sent(self):
        recipients = [
            ("MARIA", "maria@email.com")
        ]

        self.system_repository.alert_was_sent.return_value = True

        self.alert_system.email_dispatcher.send_alert_completion = Mock(
            return_value=True
        )

        self.alert_system._send_completion_alerts(
            recipients=recipients,
            activity_name="Atividade concluída",
            project_name="Projeto Teste",
        )

        self.alert_system.email_dispatcher.send_alert_completion.assert_not_called()

        self.system_repository.save_alert_history.assert_not_called()

        assert self.alert_system.stats["alerts_completion"] == 0

    def test_completion_alert_is_tracked_per_researcher(self):
        recipients = [
            ("MARIA", "maria@email.com"),
            ("JOÃO", "joao@email.com"),
        ]

        self.alert_system.email_dispatcher.send_alert_completion = Mock(
            return_value=True
        )

        self.alert_system._send_completion_alerts(
            recipients=recipients,
            activity_name="Atividade concluída",
            project_name="Projeto Teste",
        )

        assert (
            self.alert_system.email_dispatcher
            .send_alert_completion
            .call_count
            == 2
        )

        assert (
            self.system_repository.save_alert_history
            .call_count
            == 2
        )

        assert self.alert_system.stats["alerts_completion"] == 2


class TestAlertSystemIntegration:
    """Integration-like tests using mocks for all dependencies"""
    
    def test_full_workflow_with_mocks(self):
        """Test complete workflow with mocked dependencies"""
        config = Config()
        config.TEST_MODE = True
        config.SPREADSHEETS = {"teste": "id_teste"}

        system_repository = Mock()
        system_repository.get_project_state.return_value = None
        system_repository.alert_was_sent.return_value = False
        
        alert_system = AlertSystem(
            config,
            system_repository=system_repository,
        )
        
        # Mock spreadsheet_manager
        alert_system.spreadsheet_manager.load_researchers = Mock(
            return_value={
                "JOÃO": "joao@email.com",
                "MARIA": "maria@email.com",
            }
        )
        
        alert_system.spreadsheet_manager.load_activities = Mock(return_value=[
            {
                "atividade": "Atividade para iniciar",
                "status": "Não iniciada",
                "data_inicio": date.today(),
                "data_fim": date.today(),
                "responsavel_raw": "JOÃO"
            },
            {
                "atividade": "Atividade atrasada",
                "status": "Não iniciada",
                "data_inicio": date(2026, 4, 1),
                "data_fim": date(2026, 4, 5),
                "responsavel_raw": "MARIA"
            }
        ])
        
        # Mock email dispatcher
        alert_system.email_dispatcher.send_alert_start = Mock(return_value=True)
        alert_system.email_dispatcher.send_alert_delay = Mock(return_value=True)
        
        # Execute
        result = alert_system.process_all_spreadsheets()
        
        # Verify alerts were sent
        assert alert_system.email_dispatcher.send_alert_start.called
        assert alert_system.email_dispatcher.send_alert_delay.called
        
        # Verify stats
        assert result["alerts_sent"]["start"] >= 1
        assert result["alerts_sent"]["delay"] >= 1
