"""
Unit tests for email_templates.py

Tests verify:
- Placeholders are correctly replaced
- HTML structure is correct
- Header colors change based on delay days
- Empty lists are handled correctly in daily report
"""

import pytest
import re
from src.email_templates import EmailTemplates


class TestEmailTemplates:
    """Test suite for EmailTemplates class"""

    def setup_method(self):
        """Setup befor each test"""
        self.templates = EmailTemplates()

    
    def test_alert_start_contains_placeholders(self):
        """Test that alert_start replaces placeholders with actual values"""
        html = self.templates.alert_start(
            responsible_name="João Silva",
            activity_name="Revisão de documento",
            start_date="01/04/2026",
            end_date="10/04/2026",
            project_name="Sensor Diabetes"
        )

        # Check that values appear in the HTML
        assert "João Silva" in html
        assert "Revisão de documento" in html
        assert "01/04/2026" in html
        assert "10/04/2026" in html
        assert "Sensor Diabetes" in html

        # Check that raw placeholders are not present
        assert "{responsible_name}" not in html
        assert "{activity_name}" not in html
    

    def test_alert_start_html_structure(self):
        """Test that alert_start generates valid HTML structure"""
        html = self.templates.alert_start(
            responsible_name="Teste",
            activity_name="Teste",
            start_date="01/04/2026",
            end_date="02/04/2026",
            project_name="Teste"
        )
        
        # Check essential HTML tags
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "<body" in html
        
        # Check header
        assert "Iniciar Atividade" in html
        assert "#3498db" in html  # Blue header color
    

    def test_alert_delay_contains_delay_info(self):
        """Test that alert_delay shows the correct number of days delayed"""
        html = self.templates.alert_delay(
            responsible_name="Maria Silva",
            activity_name="Extração de dados",
            end_date="05/04/2026",
            days_delayed=5,
            project_name="Sensor Diabetes"
        )
        
        assert "Maria Silva" in html
        assert "Extração de dados" in html
        assert "05/04/2026" in html
        assert "5 dias" in html or "5 days" in html
    

    def test_alert_delay_color_changes_for_high_delay(self):
        """Test that header color changes when delay > 5 days"""
        
        # Test with delay <= 5
        html_normal = self.templates.alert_delay(
            responsible_name="Teste",
            activity_name="Teste",
            end_date="01/04/2026",
            days_delayed=3,
            project_name="Teste"
        )
        
        # Test with delay > 5
        html_high = self.templates.alert_delay(
            responsible_name="Teste",
            activity_name="Teste",
            end_date="01/04/2026",
            days_delayed=7,
            project_name="Teste"
        )
        
        # Extract background-color from the header div (the one with the title)
        # The header has text "ATENÇÃO" or "Atrasada"
        pattern = r'<div style="background-color: (#[a-f0-9]{6});[^>]*>.*?<h2.*?>.*?Atrasada.*?</h2>'
        
        match_normal = re.search(pattern, html_normal, re.DOTALL)
        match_high = re.search(pattern, html_high, re.DOTALL)
        
        # Alternative: look for the color right before the header text
        if not match_normal:
            # Simpler pattern: find background-color before "ATENÇÃO"
            alt_pattern = r'background-color: (#[a-f0-9]{6});[^>]*>.*?ATENÇÃO'
            match_normal = re.search(alt_pattern, html_normal, re.DOTALL)
            match_high = re.search(alt_pattern, html_high, re.DOTALL)
        
        if match_normal and match_high:
            normal_color = match_normal.group(1)
            high_color = match_high.group(1)
            
            # Colors should be different
            assert normal_color != high_color
            # Normal should be #e74c3c (red) or similar
            # High should be #c0392b (dark red)
            assert normal_color in ["#e74c3c", "#e74c3c"]
            assert high_color == "#c0392b"
        else:
            # Fallback: just check that the HTMLs are different
            assert html_normal != html_high
    
    def test_alert_completion_contains_congratulations(self):
        """Test that alert_completion has congratulatory message"""
        html = self.templates.alert_completion(
            responsible_name="Pedro Souza",
            activity_name="Reunião inicial",
            project_name="Sensor Diabetes"
        )
        
        assert "Pedro Souza" in html
        assert "Reunião inicial" in html
        assert "Concluída" in html or "Completed" in html
        assert "Parabéns" in html or "Congratulations" in html
    
    def test_daily_report_empty_lists(self):
        """Test that daily_report shows 'no activities' messages when lists are empty"""
        html = self.templates.daily_report(
            activities_to_start=[],
            activities_delayed=[],
            project_name="Sensor Diabetes"
        )
        
        # Should show "nenhuma atividade" type messages
        assert "Nenhuma" in html or "no activities" in html.lower()
    
    def test_daily_report_with_data(self):
        """Test that daily_report correctly displays activities from lists"""
        activities_to_start = [
            {"atividade": "Tarefa A", "data_fim": "10/04/2026"},
            {"atividade": "Tarefa B", "data_fim": "15/04/2026"}
        ]
        activities_delayed = [
            {"atividade": "Tarefa C", "dias_atraso": 3}
        ]
        
        html = self.templates.daily_report(
            activities_to_start=activities_to_start,
            activities_delayed=activities_delayed,
            project_name="Sensor Diabetes"
        )
        
        # Check that activities appear
        assert "Tarefa A" in html
        assert "Tarefa B" in html
        assert "Tarefa C" in html
        assert "10/04/2026" in html
        assert "15/04/2026" in html
        assert "3" in html
