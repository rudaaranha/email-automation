import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dateutil.parser import parse
import re
from src.config import Config

class SpreadsheetManager:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.client = self._authenticate()
        self._cache_reseachers = {}
        self._cache_spreadsheet = {}

    def _authenticate(self):
        """autenticação na API do google sheets"""

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.config.PATH_JSON, scope)
            client = gspread.authorize(creds)
            print('Autenticado com sucesso')
            return client
        except FileNotFoundError:
            raise Exception(f"Arquivo de credenciais não encontrado: {self.config.PATH_JSON}")
        except Exception as e:
            raise Exception(f"Falha na autenticação: {e}")
    
    def _normalize_name(self, nome: str) -> str:
        """Trata a entrada dos nomes dos pesquisadores removendo espaços e colocando tudo em maiúsculo
        
        Args:
            name: Research name (Cannot be None or empty string)
        
        Returns:
            Normalized name (upper, without spaces at beginning and the end)
            Empty String if input are None or empty
        """
        if not nome:
            return ""
    
        nome = nome.strip().upper()
        nome = " ".join(nome.split())

        return nome

    def _parse_date(self, valor: any) -> Optional[date]:
        """this function Convertes text/date for python date object
        
        Accepts:
            - None, "", "   " → None
            - date → same date
            - datetime → date
            - str "YYYY-MM-DD" → date
            - str "DD/MM/YYYY" → date
            - str "DD/MM/YY" → date
            - outher types → None
        
        Returns:
            date or None if isn't possible converte
        """ 

        if not valor:
            return None
        
        if isinstance(valor, datetime):
            return valor.date()
        
        if isinstance(valor, date):
            return valor
        
        if isinstance(valor, str):
            date_str = valor.strip()
            if not date_str:
                return None
            
            if ' ' in date_str:
                date_str = date_str.split(' ')[0]

            # teste de formatos
            formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"]

            for formato in formatos:
                try:
                    return datetime.strptime(date_str, formato).date()
                except ValueError:
                    continue

            return None
        
        return None

    def _process_responsibles(self, responsibles: str) -> List[str]:
        """Split responsible text into list of individual names
        
        Accepts texts with separators:
            - "N1, N2, N3" (comma)
            - "N1 e N2" (e)
            - "N1\nN2\nN3" (new line)
        
        Returns:
            list of normalized names (without duplicates)
        """
        
        if not responsibles:
            return []
        
        separators = [" e ", ",", ";", "|", "\n"]

        for separator in separators:
            responsibles = responsibles.replace(separator, "\n")
        
        names = [name.strip() for name in responsibles.split("\n") if name.strip()]

        unique_names = []
        for name in names:
            if name not in unique_names:
                unique_names.append(name)
        
        return [self._normalize_name(name) for name in unique_names]
    
    
    def _clean_headers(self, data):
        """
        Remove espaços dos cabeçalhos das colunas
        
        Args:
            data: Lista de dicionários do get_all_records()
        
        Returns:
            Nova lista com cabeçalhos limpos
        """
        if not data:
            return []
        
        # Pega os cabeçalhos originais
        original_headers = data[0].keys()
        
        # Cria um dicionário de tradução {original: limpo}
        header_map = {}
        for header in original_headers:
            if header is not None:
                # Remove espaços do início e fim
                clean_header = header.strip()
                header_map[header] = clean_header
        
        # Reconstruir cada linha com os cabeçalhos limpos
        cleaned_data = []
        for row in data:
            new_row = {}
            for original_key, value in row.items():
                clean_key = header_map.get(original_key, original_key)
                new_row[clean_key] = value
            cleaned_data.append(new_row)
        
        return cleaned_data


    def load_researchers(self, spreadsheet_id: str, force_reload: bool = False):
        """
        Lê a aba pesquisadores e cria um dicionário com nomes e emails
    
        Args:
            spreadsheet_id: ID da planilha do Google
            force_reload: Se True, ignora cache e força leitura do Google
    
        Returns:
            Dicionário {nome_normalizado: email_limpo}
        """

        # Verificação de Cache
        if not force_reload and spreadsheet_id in self._cache_reseachers:
            print(f"Usa cache de pesquisadores para {spreadsheet_id}")
            return self._cache_reseachers[spreadsheet_id]


        # Tentativa de abrir planilha
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
        except Exception as e:
            raise Exception(f"Erro ao abrir a planilha {spreadsheet_id}: {e}")
        

        # Acessar aba Pesquisadores
        try:
            reseachers_woorksheet = spreadsheet.worksheet(self.config.RESEARCHERS_WORKSHEET)
        except Exception as e:
            raise Exception(f"Aba '{self.config.RESEARCHERS_WORKSHEET}' não encontrada: {e}")
        
        # Leitura e processamento de dados
        data = reseachers_woorksheet.get_all_records()
        data = self._clean_headers(data)

        researchers = {}
        for row in data:
            key = row.get("RESPONSÁVEL") or row.get("Responsável") or row.get("responsável")
            if not key:
                continue

            value = row.get("E-mail") or row.get("EMAIL") or row.get("E-MAIL")
            if not value:
                continue

            key = self._normalize_name(key)
            value = value.strip().lower()

            if not key:
                continue

            if not value:
                continue

            if '@' in value and len(value.split('@')) == 2:
                researchers[key] = value
            else:
                print(f"Email inválido para {key}: {value}")

        
        # Guardar no cache
        self._cache_reseachers[spreadsheet_id] = researchers

        return researchers
    


    def load_activities(self, spreadsheet_id: str):
        """
        Retorna todas as atividades com suas respectivas informações
    
        Args:
            spreadsheet_id: ID da planilha do Google
    
        Returns:
            Lista de dicionários, cada um representando uma atividade
        """

        today = datetime.now().date()

        # Tentativa de abrir planilha
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
        except Exception as e:
            raise Exception(f"Erro ao abrir a planilha {spreadsheet_id}: {e}")
        

        # Tentativa de abrir a aba de atividades
        try:
            activities_worksheet = spreadsheet.worksheet(self.config.ACTIVITIES_WORKSHEET)
        except Exception as e:
            raise Exception(f"Erro ao tentar acessar a aba {self.config.ACTIVITIES_WORKSHEET}: {e}")

        data = activities_worksheet.get_all_records()
        data = self._clean_headers(data)

        activities = []

        for i, row in enumerate(data, start=2):
            activity_name = row.get(self.config.COLUMNS['atividade'], "")
            start_date_raw = row.get(self.config.COLUMNS['data_inicio'], "")
            end_date_raw = row.get(self.config.COLUMNS['data_fim'], "")
            status = row.get(self.config.COLUMNS['status'], "")
            if not status:
                status = "Não iniciada"
            responsible_raw = row.get(self.config.COLUMNS['responsavel'], "")


            if not activity_name:
                print(f"Linha {i} sem nome de atividade.")
                continue
            
            # Convertendo datas
            start_date = self._parse_date(start_date_raw)
            end_date = self._parse_date(end_date_raw)

            # Cálculo dos dias de atraso
            days_delayed = 0
            if end_date and status != "Concluída":
                if end_date < today:
                    days_delayed = (today - end_date).days

            # Criando o dicionário de atividades
            activity = {
                "linha": i,
                "atividade": activity_name,
                "responsavel_raw": responsible_raw,
                "data_inicio": start_date,
                "data_fim": end_date,
                "status": status,
                "dias_atraso": days_delayed
            }


            activities.append(activity)
        
        print(f"Foram carregadas {len(activities)} atividades da planilha")
        return activities
