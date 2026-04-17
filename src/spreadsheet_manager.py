import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dateutil.parser import parse
import re
from src.config import Config

class SpreadsheetManager:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.client = self._autenticate()
        self._cache_reseachers = {}
        self._cache_spreadsheet = {}

    def _auntenticate(self):
        """autenticação na API do google sheets"""

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        try:
            pass
        except:
            pass