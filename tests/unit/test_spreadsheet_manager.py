"""
Unit tests for spreadsheet_manager.py archive 

These tests verifies the auxiliaries methods without extern connections
"""

import pytest
from datetime import datetime, date
from src.spreadsheet_manager import SpreadsheetManager
from src.config import Config



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
    