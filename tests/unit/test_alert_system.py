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
        self.config.TEST_MODE = False

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
        self.system_repository.get_active_projects.return_value = [
            ProjectState(
                project="projeto1",
                spreadsheet_id="id_123",
                active=True,
            ),
            ProjectState(
                project="projeto2",
                spreadsheet_id="id_456",
                active=True,
            ),
        ]
                
        # Mock the _process_single_spreadsheet method
        self.alert_system._process_single_spreadsheet = Mock()
        
        result = self.alert_system.process_all_spreadsheets()

        assert(
            self.alert_system._process_single_spreadsheet.call_count == 2
        )

        self.alert_system._process_single_spreadsheet.assert_any_call(
            "id_123",
            "projeto1",
        )

        self.alert_system._process_single_spreadsheet.assert_any_call(
            "id_456",
            "projeto2",
        )
        assert result["total_spreadsheets"] == 2

    
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


    def test_send_start_alerts_does_not_save_history_in_test_mode(self):
        """Test mode simulates sending without saving production history."""
        self.config.TEST_MODE = True

        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = False
        self.alert_system.email_dispatcher.send_alert_start = Mock(
            return_value=True
        )

        self.alert_system._send_start_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            start_date="07/10/2026",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        self.alert_system.email_dispatcher.send_alert_start.assert_called_once()
        self.system_repository.save_alert_history.assert_not_called()

    
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


    def test_send_start_alerts_saves_history(self):
        """Test that start alert is sent and saved to history."""
        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system.email_dispatcher.send_alert_start = Mock(
            return_value=True
        )

        self.alert_system._send_start_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            start_date="07/10/2026",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        self.system_repository.alert_was_sent.assert_called_once_with(
            project="Projeto Teste",
            activity="Entrega de relatório",
            researcher="JOÃO",
            alert_type=AlertType.INICIO,
        )

        self.alert_system.email_dispatcher.send_alert_start.assert_called_once_with(
            to_email="joao@email.com",
            responsible_name="JOÃO",
            activity_name="Entrega de relatório",
            start_date="07/10/2026",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        self.system_repository.save_alert_history.assert_called_once()

        history = (
            self.system_repository.save_alert_history.call_args[0][0]
        )

        assert history.project == "Projeto Teste"
        assert history.activity == "Entrega de relatório"
        assert history.researcher == "JOÃO"
        assert history.email == "joao@email.com"
        assert history.alert_type == AlertType.INICIO

        assert self.alert_system.stats["alerts_start"] == 1


    def test_send_start_alerts_does_not_resend_if_already_sent(self):
        """Test that start alert is not sent twice."""
        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = True

        self.alert_system.email_dispatcher.send_alert_start = Mock(
            return_value=True
        )

        self.alert_system._send_start_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            start_date="07/10/2026",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        self.alert_system.email_dispatcher.send_alert_start.assert_not_called()

        self.system_repository.save_alert_history.assert_not_called()

        assert self.alert_system.stats["alerts_start"] == 0


    def test_send_start_alerts_does_not_save_history_on_failure(self):
        """Test that failed start alert is not saved to history."""
        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system.email_dispatcher.send_alert_start = Mock(
            return_value=False
        )

        self.alert_system._send_start_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            start_date="07/10/2026",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        self.alert_system.email_dispatcher.send_alert_start.assert_called_once()

        self.system_repository.save_alert_history.assert_not_called()

        assert self.alert_system.stats["alerts_start"] == 0

        assert len(self.alert_system.stats["errors"]) == 1

        assert "Failed to send start alert" in (
            self.alert_system.stats["errors"][0]
        )   


    def test_send_start_alerts_tracks_each_researcher(self):
        """Test that start alert is tracked independently per researcher."""
        recipients = [
            ("JOÃO", "joao@email.com"),
            ("MARIA", "maria@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system.email_dispatcher.send_alert_start = Mock(
            return_value=True
        )

        self.alert_system._send_start_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            start_date="07/10/2026",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        assert (
            self.alert_system.email_dispatcher
            .send_alert_start
            .call_count
            == 2
        )

        assert self.system_repository.save_alert_history.call_count == 2

        assert self.alert_system.stats["alerts_start"] == 2


    def test_send_start_alerts_only_sends_to_new_researcher(self):
        """Test that only a new researcher receives the start alert."""
        recipients = [
            ("JOÃO", "joao@email.com"),
            ("MARIA", "maria@email.com"),
        ]

        def alert_already_sent(**kwargs):
            return kwargs["researcher"] == "JOÃO"

        self.system_repository.alert_was_sent.side_effect = (
            alert_already_sent
        )

        self.alert_system.email_dispatcher.send_alert_start = Mock(
            return_value=True
        )

        self.alert_system._send_start_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            start_date="07/10/2026",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        self.alert_system.email_dispatcher.send_alert_start.assert_called_once_with(
            to_email="maria@email.com",
            responsible_name="MARIA",
            activity_name="Entrega de relatório",
            start_date="07/10/2026",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        assert self.system_repository.save_alert_history.call_count == 1

        history = (
            self.system_repository.save_alert_history.call_args[0][0]
        )

        assert history.researcher == "MARIA"
        assert history.alert_type == AlertType.INICIO

        assert self.alert_system.stats["alerts_start"] == 1


    def test_process_activity_3_days_before_deadline(self):
        """Test that activity with deadline exactly 3 days from today sends reminder."""
        today = date(2026, 10, 7)

        activity = {
            "atividade": "Entrega de relatório",
            "status": "Não iniciada",
            "data_inicio": date(2026, 10, 1),
            "data_fim": date(2026, 10, 10),
            "responsavel_raw": "JOÃO",
        }

        researchers = {
            "JOÃO": "joao@email.com",
        }

        self.alert_system._send_3_days_alerts = Mock()
        self.alert_system._send_1_day_alerts = Mock()
        self.alert_system._send_delay_alerts = Mock()
        self.alert_system._send_completion_alerts = Mock()

        self.alert_system._process_activity(
            activity,
            researchers,
            "projeto_teste",
            today,
        )

        self.alert_system._send_3_days_alerts.assert_called_once_with(
            [("JOÃO", "joao@email.com")],
            "Entrega de relatório",
            "10/10/2026",
            "projeto_teste",
            today,
        )

        self.alert_system._send_1_day_alerts.assert_not_called()
        self.alert_system._send_delay_alerts.assert_not_called()
        self.alert_system._send_completion_alerts.assert_not_called()


    def test_process_activity_does_not_send_3_days_reminder_with_4_days_remaining(self):
        """Test that 4 days before deadline does not send 3-day reminder."""
        today = date(2026, 10, 6)

        activity = {
            "atividade": "Entrega de relatório",
            "status": "Não iniciada",
            "data_inicio": date(2026, 10, 1),
            "data_fim": date(2026, 10, 10),
            "responsavel_raw": "JOÃO",
        }

        researchers = {
            "JOÃO": "joao@email.com",
        }

        self.alert_system._send_3_days_alerts = Mock()
        self.alert_system._send_1_day_alerts = Mock()
        self.alert_system._send_delay_alerts = Mock()

        self.alert_system._process_activity(
            activity,
            researchers,
            "projeto_teste",
            today,
        )

        self.alert_system._send_3_days_alerts.assert_not_called()
        self.alert_system._send_1_day_alerts.assert_not_called()
        self.alert_system._send_delay_alerts.assert_not_called()


    def test_process_activity_does_not_send_3_days_reminder_with_2_days_remaining(self):
        """Test that 2 days before deadline does not send 3-day reminder."""
        today = date(2026, 10, 8)

        activity = {
            "atividade": "Entrega de relatório",
            "status": "Não iniciada",
            "data_inicio": date(2026, 10, 1),
            "data_fim": date(2026, 10, 10),
            "responsavel_raw": "JOÃO",
        }

        researchers = {
            "JOÃO": "joao@email.com",
        }

        self.alert_system._send_3_days_alerts = Mock()
        self.alert_system._send_1_day_alerts = Mock()

        self.alert_system._process_activity(
            activity,
            researchers,
            "projeto_teste",
            today,
        )

        self.alert_system._send_3_days_alerts.assert_not_called()


    def test_send_3_days_alerts(self):
        """Test that 3-day reminder is sent and saved to history."""
        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        reference_date = date(2026, 10, 7)

        self.alert_system.email_dispatcher.send_alert_3_days = Mock(
            return_value=True
        )

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system._send_3_days_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
            reference_date=reference_date,
        )

        self.system_repository.alert_was_sent.assert_called_once_with(
            project="Projeto Teste",
            activity="Entrega de relatório",
            researcher="JOÃO",
            alert_type=AlertType.FALTA_3_DIAS,
        )

        self.alert_system.email_dispatcher.send_alert_3_days.assert_called_once_with(
            to_email="joao@email.com",
            responsible_name="JOÃO",
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        self.system_repository.save_alert_history.assert_called_once()

        history = (
            self.system_repository.save_alert_history.call_args[0][0]
        )

        assert history.project == "Projeto Teste"
        assert history.activity == "Entrega de relatório"
        assert history.researcher == "JOÃO"
        assert history.email == "joao@email.com"
        assert history.alert_type == AlertType.FALTA_3_DIAS
        assert history.reference_date == reference_date

        assert self.alert_system.stats["alerts_3_days"] == 1


    def test_send_3_days_alerts_does_not_resend_if_already_sent(self):
        """Test that 3-day reminder is not sent twice."""
        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = True

        self.alert_system.email_dispatcher.send_alert_3_days = Mock(
            return_value=True
        )

        self.alert_system._send_3_days_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
            reference_date=date(2026, 10, 7),
        )

        self.alert_system.email_dispatcher.send_alert_3_days.assert_not_called()
        self.system_repository.save_alert_history.assert_not_called()

        assert self.alert_system.stats["alerts_3_days"] == 0


    def test_send_3_days_alerts_does_not_save_history_on_failure(self):
        """Test that failed 3-day reminder is not saved to history."""
        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system.email_dispatcher.send_alert_3_days = Mock(
            return_value=False
        )

        self.alert_system._send_3_days_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
            reference_date=date(2026, 10, 7),
        )

        self.alert_system.email_dispatcher.send_alert_3_days.assert_called_once()

        self.system_repository.save_alert_history.assert_not_called()

        assert self.alert_system.stats["alerts_3_days"] == 0

        assert len(self.alert_system.stats["errors"]) == 1
        assert "Failed to send 3-day reminder" in (
            self.alert_system.stats["errors"][0]
        )


    def test_send_3_days_alerts_tracks_each_researcher(self):
        """Test that 3-day reminder is tracked independently per researcher."""
        recipients = [
            ("JOÃO", "joao@email.com"),
            ("MARIA", "maria@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system.email_dispatcher.send_alert_3_days = Mock(
            return_value=True
        )

        self.alert_system._send_3_days_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
            reference_date=date(2026, 10, 7),
        )

        assert (
            self.alert_system.email_dispatcher
            .send_alert_3_days
            .call_count
            == 2
        )

        assert self.system_repository.save_alert_history.call_count == 2

        assert self.alert_system.stats["alerts_3_days"] == 2


    def test_process_activity_1_day_before_deadline(self):
        """Test that activity with deadline exactly 1 day from today sends reminder."""
        today = date(2026, 10, 9)

        activity = {
            "atividade": "Entrega de relatório",
            "status": "Não iniciada",
            "data_inicio": date(2026, 10, 1),
            "data_fim": date(2026, 10, 10),
            "responsavel_raw": "JOÃO",
        }

        researchers = {
            "JOÃO": "joao@email.com",
        }

        self.alert_system._send_3_days_alerts = Mock()
        self.alert_system._send_1_day_alerts = Mock()
        self.alert_system._send_delay_alerts = Mock()
        self.alert_system._send_completion_alerts = Mock()

        self.alert_system._process_activity(
            activity,
            researchers,
            "projeto_teste",
            today,
        )

        self.alert_system._send_1_day_alerts.assert_called_once_with(
            [("JOÃO", "joao@email.com")],
            "Entrega de relatório",
            "10/10/2026",
            "projeto_teste",
            today,
        )

        self.alert_system._send_3_days_alerts.assert_not_called()
        self.alert_system._send_delay_alerts.assert_not_called()
        self.alert_system._send_completion_alerts.assert_not_called()


    def test_process_activity_does_not_send_1_day_reminder_with_2_days_remaining(self):
        """Test that 2 days before deadline does not send 1-day reminder."""
        today = date(2026, 10, 8)

        activity = {
            "atividade": "Entrega de relatório",
            "status": "Não iniciada",
            "data_inicio": date(2026, 10, 1),
            "data_fim": date(2026, 10, 10),
            "responsavel_raw": "JOÃO",
        }

        researchers = {
            "JOÃO": "joao@email.com",
        }

        self.alert_system._send_1_day_alerts = Mock()
        self.alert_system._send_delay_alerts = Mock()

        self.alert_system._process_activity(
            activity,
            researchers,
            "projeto_teste",
            today,
        )

        self.alert_system._send_1_day_alerts.assert_not_called()
        self.alert_system._send_delay_alerts.assert_not_called()


    def test_send_1_day_alerts(self):
        """Test that 1-day reminder is sent and saved to history."""
        recipients = [
            ("MARIA", "maria@email.com"),
        ]

        reference_date = date(2026, 10, 9)

        self.alert_system.email_dispatcher.send_alert_1_day = Mock(
            return_value=True
        )

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system._send_1_day_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
            reference_date=reference_date,
        )

        self.system_repository.alert_was_sent.assert_called_once_with(
            project="Projeto Teste",
            activity="Entrega de relatório",
            researcher="MARIA",
            alert_type=AlertType.FALTA_1_DIA,
        )

        self.alert_system.email_dispatcher.send_alert_1_day.assert_called_once_with(
            to_email="maria@email.com",
            responsible_name="MARIA",
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
        )

        self.system_repository.save_alert_history.assert_called_once()

        history = (
            self.system_repository.save_alert_history.call_args[0][0]
        )

        assert history.project == "Projeto Teste"
        assert history.activity == "Entrega de relatório"
        assert history.researcher == "MARIA"
        assert history.email == "maria@email.com"
        assert history.alert_type == AlertType.FALTA_1_DIA
        assert history.reference_date == reference_date

        assert self.alert_system.stats["alerts_1_day"] == 1    


    def test_send_1_day_alerts_does_not_resend_if_already_sent(self):
        """Test that 1-day reminder is not sent twice."""
        recipients = [
            ("MARIA", "maria@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = True

        self.alert_system.email_dispatcher.send_alert_1_day = Mock(
            return_value=True
        )

        self.alert_system._send_1_day_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
            reference_date=date(2026, 10, 9),
        )

        self.alert_system.email_dispatcher.send_alert_1_day.assert_not_called()
        self.system_repository.save_alert_history.assert_not_called()

        assert self.alert_system.stats["alerts_1_day"] == 0


    def test_send_1_day_alerts_does_not_save_history_on_failure(self):
        """Test that failed 1-day reminder is not saved to history."""
        recipients = [
            ("MARIA", "maria@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system.email_dispatcher.send_alert_1_day = Mock(
            return_value=False
        )

        self.alert_system._send_1_day_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
            reference_date=date(2026, 10, 9),
        )

        self.alert_system.email_dispatcher.send_alert_1_day.assert_called_once()

        self.system_repository.save_alert_history.assert_not_called()

        assert self.alert_system.stats["alerts_1_day"] == 0

        assert len(self.alert_system.stats["errors"]) == 1
        assert "Failed to send 1-day reminder" in (
            self.alert_system.stats["errors"][0]
        )


    def test_send_1_day_alerts_tracks_each_researcher(self):
        """Test that 1-day reminder is tracked independently per researcher."""
        recipients = [
            ("MARIA", "maria@email.com"),
            ("JOÃO", "joao@email.com"),
        ]

        self.system_repository.alert_was_sent.return_value = False

        self.alert_system.email_dispatcher.send_alert_1_day = Mock(
            return_value=True
        )

        self.alert_system._send_1_day_alerts(
            recipients=recipients,
            activity_name="Entrega de relatório",
            end_date="10/10/2026",
            project_name="Projeto Teste",
            reference_date=date(2026, 10, 9),
        )

        assert (
            self.alert_system.email_dispatcher
            .send_alert_1_day
            .call_count
            == 2
        )

        assert self.system_repository.save_alert_history.call_count == 2

        assert self.alert_system.stats["alerts_1_day"] == 2


    def test_completed_activity_does_not_send_deadline_reminders(self):
        """Test that completed activities do not receive deadline reminders."""
        today = date(2026, 10, 7)

        activity = {
            "atividade": "Entrega de relatório",
            "status": "Concluída",
            "data_inicio": date(2026, 10, 1),
            "data_fim": date(2026, 10, 10),
            "responsavel_raw": "JOÃO",
        }

        researchers = {
            "JOÃO": "joao@email.com",
        }

        self.alert_system._send_3_days_alerts = Mock()
        self.alert_system._send_1_day_alerts = Mock()

        self.alert_system._process_activity(
            activity,
            researchers,
            "projeto_teste",
            today,
        )

        self.alert_system._send_3_days_alerts.assert_not_called()
        self.alert_system._send_1_day_alerts.assert_not_called()

        
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


    def test_send_delay_alerts_allows_new_alert_on_next_day(self):
        """Test that delay alert can be sent again on a different day."""
        recipients = [
            ("JOÃO", "joao@email.com"),
        ]

        self.alert_system.email_dispatcher.send_alert_delay = Mock(
            return_value=True
        )

        # Alert was already sent on the previous day.
        def alert_was_sent(**kwargs):
            return kwargs["reference_date"] == date(2026, 10, 8)

        self.system_repository.alert_was_sent.side_effect = alert_was_sent

        self.alert_system._send_delay_alerts(
            recipients=recipients,
            activity_name="Atividade Teste",
            end_date="05/10/2026",
            days_delayed=4,
            project_name="Projeto Teste",
            reference_date=date(2026, 10, 9),
        )

        self.alert_system.email_dispatcher.send_alert_delay.assert_called_once()

        self.system_repository.save_alert_history.assert_called_once()

        history = self.system_repository.save_alert_history.call_args[0][0]

        assert history.reference_date == date(2026, 10, 9)
        assert history.alert_type == AlertType.ATRASO

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
        """Test processing a single project from PROJECTS"""
        self.system_repository.get_project_state.return_value = ProjectState(
            project="projeto1",
            spreadsheet_id="id_123",
            active=True,
        )
        
        # Mock _process_single_spreadsheet
        self.alert_system._process_single_spreadsheet = Mock()
        
        result = self.alert_system.process_single_project(
            "projeto1"
        )
        
        # Should have been called once with correct ID
        self.system_repository.get_project_state.assert_called_once_with(
            "projeto1"
        )
        
        self.alert_system._process_single_spreadsheet.assert_called_once_with(
            "id_123", 
            "projeto1",
        )
        
        assert result["project"] == "projeto1"
        assert result["total_spreadsheets"] == 1

    
    def test_process_single_project_not_found(self):
        """Test that an unknown project returns an error."""
        self.system_repository.get_project_state.return_value = None

        self.alert_system._process_single_spreadsheet = Mock()
      
        result = self.alert_system.process_single_project(
            "projeto_inexistente"
        )
        
        assert "error" in result

        assert (
            result["error"]
            == "Project 'projeto_inexistente' not found in control spreadsheet"
        )

        self.alert_system._process_single_spreadsheet.assert_not_called()


    def test_process_single_project_respects_active_true(self):
        """Test that an active project is processed."""
        
        self.system_repository.get_project_state.return_value = ProjectState(
            project="projeto_ativo",
            spreadsheet_id="id_123",
            active=True,
        )

        self.alert_system._process_single_spreadsheet = Mock()

        result = self.alert_system.process_single_project(
            "projeto_ativo"
        )

        self.alert_system._process_single_spreadsheet.assert_called_once_with(
            "id_123",
            "projeto_ativo",
        )

        assert result["project"] == "projeto_ativo"


    def test_process_single_project_skips_inactive_project(self):
        """Test that an inactive project is not processed."""
        
        self.system_repository.get_project_state.return_value = ProjectState(
            project="projeto_inativo",
            spreadsheet_id="id_123",
            active=False,
        )

        self.alert_system._process_single_spreadsheet = Mock()

        result = self.alert_system.process_single_project(
            "projeto_inativo"
        )

        self.alert_system._process_single_spreadsheet.assert_not_called()

        assert result["project"] == "projeto_inativo"
        assert result["total_activities"] == 0

        assert result["alerts_sent"]["start"] == 0
        assert result["alerts_sent"]["delay"] == 0
        assert result["alerts_sent"]["completion"] == 0
        assert result["alerts_sent"]["3_days"] == 0
        assert result["alerts_sent"]["1_day"] == 0

   
    def test_stats_reset_between_executions(self):
        """Test that statistics are reset between process executions"""
        self.system_repository.get_active_projects.return_value = [
            ProjectState(
                project="projeto1",
                spreadsheet_id="id_123",
                active=True,
            )
        ]

        self.alert_system._process_single_spreadsheet = Mock()

        # First execution
        self.alert_system.process_all_spreadsheets()

        # Simulate alerts from the first execution
        self.alert_system.stats["alerts_start"] = 5

        # Second execution
        self.alert_system.process_all_spreadsheets()

        # Statistics must have been reset
        assert self.alert_system.stats["alerts_start"] == 0
        assert self.alert_system.stats["alerts_delay"] == 0
        assert self.alert_system.stats["alerts_completion"] == 0
        assert self.alert_system.stats["alerts_3_days"] == 0
        assert self.alert_system.stats["alerts_1_day"] == 0
        assert len(self.alert_system.stats["errors"]) == 0


    def test_inactive_project_is_not_processed(self):
        """Test that inactive projects are not processed."""
        self.system_repository.get_active_projects.return_value = []

        self.alert_system._process_single_spreadsheet = Mock()

        result = self.alert_system.process_all_spreadsheets()

        self.alert_system._process_single_spreadsheet.assert_not_called()

        assert result["total_spreadsheets"] == 0


    def test_active_project_is_processed(self):
        """Test that active projects are processed."""
        self.system_repository.get_active_projects.return_value = [
            ProjectState(
                project="projeto_ativo",
                spreadsheet_id="id_123",
                active=True,
            )    
        ]
        
        self.alert_system._process_single_spreadsheet = Mock()

        result = self.alert_system.process_all_spreadsheets()

        self.alert_system._process_single_spreadsheet.assert_called_once_with(
            "id_123",
            "projeto_ativo",
        )

        assert result["total_spreadsheets"] == 1


    def test_control_worksheets_are_ensured_before_processing(self):
        """Test that control worksheets are ensured before processing."""
        self.system_repository.get_active_projects.return_value = [
            ProjectState(
                project="projeto1",
                spreadsheet_id="id_123",
                active=True,
            )
        ]

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

        system_repository = Mock()
        system_repository.get_active_projects.return_value = [
            ProjectState(
                project="teste",
                spreadsheet_id="id_teste",
                active=True,
            )
        ]

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
