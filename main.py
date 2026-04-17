import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Carrega o arquivo .env
load_dotenv()

EMAIL_LAB = os.getenv("EMAIL_LAB")
SENHA_APP = os.getenv("SENHA_APP_LAB")

# IDs das Planilhas usadas nos projetos
PLANILHAS = [
    os.getenv("ID_PLANILHA_SENSOR_DIABETES")
]

PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_JSON = os.path.join(PROJETO, 'credenciais.json')

# Função para verificar as planilhas
def verificar_planilhas(client, spreadsheet_id):
    if not spreadsheet_id:
        return

    try:
        planilha = client.open_by_key(spreadsheet_id)
        print(f"\n--- Processando: {planilha.title} ---")

        aba_tarefas = planilha.worksheet("ENTREGA DE ATIVIDADES")
        aba_contatos = planilha.worksheet("PESQUISADORES")

        # get_all_records transforma a primeira linha da planilha em chaves dict
        tarefas = aba_tarefas.get_all_records()
        contatos = {row['Responsável']: row['E-mail'] for row in aba_contatos.get_all_records()}

        hoje = datetime.now().date()

        for tarefa in tarefas:
            pass
    
    except Exception as e:
        print(f"Erro ao acessar Planilha {spreadsheet_id}: {e}")

# Definição do escopo de acesso ao Drive e Planilhas
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Carrega as credenciais do arquivo JSON gerado no Google Cloud Console
CREDS = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', SCOPE)
CLIENTE = gspread.authorize(CREDS)



# Função para enviar os emails


