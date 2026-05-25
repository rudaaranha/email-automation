"""
Unit tests for spreadsheet_manager.py archive 

These tests verifies the auxiliaries methods without extern connections
"""

import pytest
from datetime import datetime, date
from src.spreadsheet_manager import SpreadsheetManager
from src.config import Config
from unittest.mock import Mock


class TestNormalizeName:
    """
    Tests for _normalize_name method
    
    The method should:
    - Remove leading and trailing spaces
    - Convert all letters to uppercase
    - Return empty string for None or empty inputs
    - Preserve accents
    """

    def test_normalize_with_spaces(self, spreadsheet_manager):
        restult = spreadsheet_manager._normalize_name("  RUDÁ ARANHA  ")
        assert restult == "RUDÁ ARANHA"

    def test_normalize_lowercase(self, spreadsheet_manager):
        result = spreadsheet_manager._normalize_name("rudá aranha")
        assert result == "RUDÁ ARANHA"
    
    def test_normalize_mixed_case(self, spreadsheet_manager):
        result = spreadsheet_manager._normalize_name("RuDá aRanHA")
        assert result == "RUDÁ ARANHA"
    
    def test_normalize_with_accents(self, spreadsheet_manager):
        result = spreadsheet_manager._normalize_name("João Silva")
        assert result == "JOÃO SILVA"

    def test_normalize_spaces_beetween_names(self, spreadsheet_manager):
        result = spreadsheet_manager._normalize_name("João   Silva")
        assert result == "JOÃO SILVA"

    def test_normalize_none_value(self, spreadsheet_manager):
        result = spreadsheet_manager._normalize_name(None)
        assert result == ""
    
    def test_normalize_empty_names(self, spreadsheet_manager):
        result = spreadsheet_manager._normalize_name("")
        assert result == ""

    def test_normalize_name_with_only_spaces(self, spreadsheet_manager):
        result = spreadsheet_manager._normalize_name("     ")
        assert result == ""
    
    def test_normalize_preserves_middle_spaces(self, spreadsheet_manager):
        result = spreadsheet_manager._normalize_name("Ana Carolina")
        assert result == "ANA CAROLINA"
        assert " " in result
    
    def test_normalize_already_normalized(self, spreadsheet_manager):
        original = "RUDÁ ARANHA"
        result = spreadsheet_manager._normalize_name(original)
        assert result == original


class TestParseDate:
    """
    Tests for _parse_date method

    The method should:
    - Handle None and empty string inputs
    - Parse American format (YYYY-MM-DD)
    - Parse Brazilian format (DD/MM/YYYY)
    - Ignore time information when present
    - Return None for invalid dates
    - Return the same date object if already a date
    - Extract date from datetime object
    """

    def test_parse_date_none_value(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date(None)
        assert result == None
    
    def test_parse_date_empty_string(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date("")
        assert result == None
    
    def test_parse_date_only_spaces(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date("     ")
        assert result == None
    
    def test_parse_date_american_format(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date("2026-04-02")
        assert result == date(2026, 4, 2)
    
    def test_parse_date_brazilian_format(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date("02/04/2026")
        assert result == date(2026, 4, 2)

    def test_parse_date_with_hour(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date("2026-04-02 15:30:00")
        assert result == date(2026, 4, 2)
    
    def test_parse_date_with_hour_and_spaces(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date(" 2026-04-02 00:00:00 ")
        assert result == date(2026, 4, 2)
    
    def test_parse_date_invalid_date(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date("30/02/2026")
        assert result == None
    
    def test_parse_date_with_text(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date("30/02/2o26")
        assert result == None
    
    def test_parse_date_already_exists(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date(date(2026, 4, 2))
        assert result == date(2026, 4, 2)
    
    def test_parse_date_datetime_exists(self, spreadsheet_manager):
        result = spreadsheet_manager._parse_date(datetime(2026, 4, 2, 14, 30))
        assert result == date(2026, 4, 2)


class TestProcessResponsibles:
    """
    Tests for _process_responsibles method

    The method should:
    - Split names separated by comma, "e", or newline
    - Remove duplicates
    - Normalize each name (uppercase, stripped)
    - Return empty list for empty or None input
    """

    def test_process_responsibles_empty_value(self, spreadsheet_manager):
        result = spreadsheet_manager._process_responsibles("")
        assert result == []
    
    def test_process_responsibles_none_value(self, spreadsheet_manager):
        result = spreadsheet_manager._process_responsibles(None)
        assert result == []

    def test_process_responsibles_unique_name(self, spreadsheet_manager):
        result = spreadsheet_manager._process_responsibles("JOÃO SILVA")
        assert result == ["JOÃO SILVA"]
    
    def test_process_responsibles_names_separeted_with_comma(self, spreadsheet_manager):
         result = spreadsheet_manager._process_responsibles("João, Ana Carolina, Augusto")
         assert result == ["JOÃO", "ANA CAROLINA", "AUGUSTO"]

    def test_process_responsibles_names_separeted_with_e(self, spreadsheet_manager):
        result = spreadsheet_manager._process_responsibles("João e Maria")
        assert result == ["JOÃO", "MARIA"]

    def test_process_responsibles_names_separeted_with_line_break(self, spreadsheet_manager):
        result = spreadsheet_manager._process_responsibles("João\nAna Carolina\nAugusto")
        assert result == ["JOÃO", "ANA CAROLINA", "AUGUSTO"]

    def test_process_responsibles_without_duplicates(self, spreadsheet_manager):
        result = spreadsheet_manager._process_responsibles("João, João, Maria")
        assert result == ["JOÃO", "MARIA"]
    
    def test_process_responsibles_without_spaces(self, spreadsheet_manager):
        result = spreadsheet_manager._process_responsibles("João , Maria")
        assert result == ["JOÃO", "MARIA"]
    
    def test_process_responsibles_mixed_separeted_names(self, spreadsheet_manager):
        result = spreadsheet_manager._process_responsibles("João, Ana Carolina e Augusto")
        assert result == ["JOÃO", "ANA CAROLINA", "AUGUSTO"]


class TestCleanHeaders:
    """
    Tests for _clean_headers method

    The method should:
    - Remove leading/trailing spaces from column headers
    - Preserve data values unchanged
    - Handle empty lists gracefully
    - Not modify already clean headers
    """

    def test_clean_headers_empty_list(self, spreadsheet_manager):
        result = spreadsheet_manager._clean_headers([])
        assert result == []
    
    def test_clean_headers_with_spaces_begin(self, spreadsheet_manager):
        result = spreadsheet_manager._clean_headers([{" DEMANDA": "TAREFA 1"}])
        assert result == [{"DEMANDA": "TAREFA 1"}]

    def test_clean_headers_with_spaces_end(self, spreadsheet_manager):
        result = spreadsheet_manager._clean_headers([{"DEMANDA ": "TAREFA 1"}])
        assert result == [{"DEMANDA": "TAREFA 1"}]

    def test_clean_headers_with_spaces(self, spreadsheet_manager):
        result = spreadsheet_manager._clean_headers([{" DEMANDA ": "TAREFA 1"}])
        assert result == [{"DEMANDA": "TAREFA 1"}]
    
    def test_clean_headers_already_normalized(self, spreadsheet_manager):
        result = spreadsheet_manager._clean_headers([{"DEMANDA": "TAREFA 1"}])
        assert result == [{"DEMANDA": "TAREFA 1"}]
    
    def test_clean_headers_with_multiples_task(self, spreadsheet_manager):
        result = spreadsheet_manager._clean_headers([{"DEMANDA": "TAREFA 1"}, {"DEMANDA": "TAREFA 2"}])
        assert result == [{"DEMANDA": "TAREFA 1"}, {"DEMANDA": "TAREFA 2"}]
    
    def test_clean_headers_only_keys(self, spreadsheet_manager):
        result = spreadsheet_manager._clean_headers([{"DEMANDA ": "TAREFA 1 "}, {"DEMANDA": "TAREFA 2 "}])
        assert result == [{"DEMANDA": "TAREFA 1 "}, {"DEMANDA": "TAREFA 2 "}]


class TestLoadResearchers:
    """Test for method load_researchers"""

    fake_data = [
        {"Responsável": "João Silva", "E-mail": "joaos@mail.com"},
        {"Responsável": "ANA CAROLINA", "E-mail": "anac@mail.com"},
        {"Responsável": "augusto carlos", "E-mail": "augusto_c@mail.com"}
    ]

    
    def test_load_researchers_without_problems(self, spreadsheet_manager):

        mock_worksheet = Mock()
        mock_spreadsheet = Mock()
        mock_client = Mock()

        mock_worksheet.get_all_records.return_value = self.fake_data
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet

        # substituindo o client real pelo mock
        spreadsheet_manager.client = mock_client

        result = spreadsheet_manager.load_researchers("id_falso")

        assert len(result) == 3
        assert result["JOÃO SILVA"] == "joaos@mail.com"
        assert result["ANA CAROLINA"] == "anac@mail.com"
        assert result["AUGUSTO CARLOS"] == "augusto_c@mail.com"


    def test_load_researchers_with_problems(self, spreadsheet_manager):
        """Rows without name or email should be ignored"""
    
        # data with problem
        fake_data = [
            {"Responsável": "João Silva", "E-mail": "joao@mail.com"},            # ok
            {"Responsável": "", "E-mail": "vazio@mail.com"},                     # empty name
            {"Responsável": "SEM_EMAIL", "E-mail": ""},                          # empty email
            {"Responsável": "  ", "E-mail": "soh_espaco@mail.com"},              # only spaces
            {"Responsável": "INVALIDO", "E-mail": "sem_arroba"},                 # email without @
            {"Responsável": "MARIA SILVA", "E-mail": "maria@mail.com"},          # ok
        ]
        
        mock_worksheet = Mock()
        mock_spreadsheet = Mock()
        mock_client = Mock()
        
        mock_worksheet.get_all_records.return_value = fake_data
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        spreadsheet_manager.client = mock_client
        
        result = spreadsheet_manager.load_researchers("id_falso")
        
        # Apenas 2 linhas válidas (João e Maria) devem estar no resultado
        assert len(result) == 2
        assert result["JOÃO SILVA"] == "joao@mail.com"
        assert result["MARIA SILVA"] == "maria@mail.com"
        assert "SEM_EMAIL" not in result
        assert "INVALIDO" not in result


    def test_load_researchers_cache(self, spreadsheet_manager):
        """Second call with same ID should use cache, not call Google again"""
        
        from unittest.mock import call
        
        fake_data = [
            {"Responsável": "João Silva", "E-mail": "joao@mail.com"},
            {"Responsável": "Maria Silva", "E-mail": "maria@mail.com"},
        ]
        
        mock_worksheet = Mock()
        mock_spreadsheet = Mock()
        mock_client = Mock()
        
        mock_worksheet.get_all_records.return_value = fake_data
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        spreadsheet_manager.client = mock_client
        
        # First call - Google
        result1 = spreadsheet_manager.load_researchers("id_123")
        
        # Second call - cache
        result2 = spreadsheet_manager.load_researchers("id_123")
        
        # Third call with force_reload - Google again
        result3 = spreadsheet_manager.load_researchers("id_123", force_reload=True)
        
        assert len(result1) == 2
        assert len(result2) == 2
        assert len(result3) == 2
        
        # Verify if open_by_key was called 2 times 
        # The second one (cache) wouldn't be called
        assert mock_client.open_by_key.call_count == 2
        
        # Verify if get_all_records was called 2 times
        assert mock_worksheet.get_all_records.call_count == 2


    def test_load_researchers_different_ids_separate_cache(self, spreadsheet_manager):
        """Different spreadsheet IDs should have separate caches"""
        
        fake_data_1 = [
            {"Responsável": "João Silva", "E-mail": "joao@mail.com"},
        ]
        
        fake_data_2 = [
            {"Responsável": "Maria Silva", "E-mail": "maria@mail.com"},
        ]
        
        def get_mock_client(data):
            mock_worksheet = Mock()
            mock_spreadsheet = Mock()
            mock_client = Mock()
            
            mock_worksheet.get_all_records.return_value = data
            mock_spreadsheet.worksheet.return_value = mock_worksheet
            mock_client.open_by_key.return_value = mock_spreadsheet
            
            return mock_client
        
        # First spreadsheet - ID_1
        spreadsheet_manager.client = get_mock_client(fake_data_1)
        result1 = spreadsheet_manager.load_researchers("id_1")
        
        # Second spreadsheet - ID_2
        spreadsheet_manager.client = get_mock_client(fake_data_2)
        result2 = spreadsheet_manager.load_researchers("id_2")
        
        
        assert result1["JOÃO SILVA"] == "joao@mail.com"
        assert result2["MARIA SILVA"] == "maria@mail.com"
        assert len(result1) == 1
        assert len(result2) == 1

class TestLoadActivities:
    pass