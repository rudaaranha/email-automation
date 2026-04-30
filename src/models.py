"""
Modelos de dados para a API de Automação de alertas

Definição de todas as entruturas de daos usadas na API usando Pydantic para validação e 
geração de documentação de forma automática
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, EmailStr


class AlertType(str, Enum):
    """Tipos de alerta que podem ser enviados"""
    INICIO = "inicio"
    ATRASO = "atraso"
    CONCLUSAO = "conclusao"
    FALTA_3_DIAS = "falta_3_dias"
    FALTA_1_DIA = "falta_1_dia"

class ActivityStatus(str, Enum):
    """Possíveis status de uma atividade"""
    PENDENTE = "Pendente"
    ANDAMENTO = "Andamento"
    CONCLUIDA = "Concluida"
    ATRASADA = "Atrasada"

class ExecutionMode(str, Enum):
    """Modo de execução do sistema"""
    TEST = "test"
    PRODUCTION = "production"


# Request Models

class ExecuteRequest(BaseModel):
    """
    Modelo para requisição POST/execute

    O client pode enviar dados para controle de execução
    """

    project: Optional[str] = Field(
        default=None,
        description="Nome do projeto especifico para processar"
    )
    force: bool = Field(
        default=False,
        description="Força a execução mesmo fora do horário programado"
    )
    mode: ExecutionMode = Field(
        default=ExecutionMode.PRODUCTION,
        description="Modo de execução (test ou production)"
    )

    @field_validator('project')
    @classmethod
    def validate_project(cls, v: Optional[str]) -> Optional[str]:
        """Valida se o projeto tem formato válido"""
        if v is not None and not v.strip():
            raise ValueError("Nome do projeto não pode ser vazio")
        return v.lower().strip() if v else v
    

class TestEmailRequest(BaseModel):
    """
    Modelo para requisição Post/test-email
    Testa o envio dos emails
    """

    to_email: EmailStr = Field(
        description="Email de destino para teste"
    )
    alert_type: AlertType = Field(
        default=AlertType.INICIO,
        description="Tipo de alerta para ser testado"
    )
    activity_name: str = Field(
        default="Atividade de Teste",
        description="Nome da atividade"
   )


# Response models


class ActivityResponse(BaseModel):
    '''
    Modelo de atividade para resposta de API

    Representa uma atividade da planilha com dados enriquecidos
    '''    
    id: int = Field(description="Número da linha na planilha")
    nome: str = Field(description="Nome da atividade")
    responsavel: str = Field(description="Nome do responsável pela atividade")
    email_responsavel: Optional[str] = Field(
        default=None,
        description="Email do responsável"
    )
    data_inicio: Optional[date] = Field(default=None, description="Data de início")
    data_fim: Optional[date] = Field(default=None, description="Data de entrega") 
    status: ActivityStatus = Field(description="Status atual")
    dias_atraso: int = Field(
        default=0, 
        description="Dias em atraso"
    )
    project: str = Field(description="Nome do Projeto")

class Config:
    """Configuração adicional do modelo"""
    json_chema_extra = {
        "example": {
            "id": 2,
            "nome": "Revisão da pergunda de pesquisa",
            "responsavel": "João Augusto",
            "email_responsavel": "João@lab.com",
            "data_inicio": "2026-04-01",
            "data_fim": "2026-04-02",
            "status": "Concluída",
            "dias_atraso": 0,
            "project": "sensor_diabetes"
        }
    }


class AlertResult(BaseModel):
    """Resultado de um alerta enviado"""

    type: AlertType = Field(description="Tipo de alerta")
    to: str = Field(description="Destinatário")
    activity: str = Field(description="Atividade relacionada")
    success: bool = Field(description="Se o envio foi bem sucedido")
    error: Optional[str] = Field(default=None, description="Mensagem de erro")


class ExecuteResponse(BaseModel):
    """
    Resposta para requisição POST/execute

    Retorna Estatísticas de execução
    """

    sucess: bool = Field(description="Se a execução foi bem sucedida")
    timestamp: datetime = Field(description="Momento da execução")
    mode: ExecutionMode = Field(description="Modo de execução usado")

    # Estatísticas
    projects_processed: int = Field(description="Quantidade de projetos processados")
    total_activities: int = Field(description="Total de atividades encontradas")
    alerts_sent: Dict[str, int] = Field(
        default_factory=dict,
        description="Contagem de alertas por tipo"
    )

    # Detalhes opcionais
    errors: List[str] = Field(default_factory=list, description="Erros encontrados")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detalhes adicionais da execução"
    )

class StatusResponse(BaseModel):
    """
    Resposta para GET/status
    Mostra o estado atual do sistema
    """
    system: str = Field(default="Sistema de Alertas de Atividades")
    version: str = Field(default="1.0.0")
    status: str =Field(description="'healthy' ou 'unhealthy'")
    timestamp: datetime = Field(description="Momento de consulta")

    # Configurações ativas
    test_mode: bool = Field(description="Se está em modo de teste")
    configured_projects: List[str] = Field(description="Horários agendados")

    # Estatísticas
    total_alerts_sent_today: int = Field(default=0)
    last_execution: Optional[datetime] = Field(default=None)


class HealthResponse(BaseModel):
    """
    Resposta para GET/health

    Health check
    """
    status: str = Field(description="'ok' se tudo estiver funcionando")
    google_sheets_api: bool = Field(description="Se a API do sheets está acessível")
    smtp_configured: bool = Field(description="Se SMTP está configurado")
    sheets_accessible: List[str] = Field(description="Planilhas acessíveis")

# Internal Models (para uso interno do sistema)

class RawActivity(BaseModel):
    """
    Modelo interno para atividade sem tratamento vindo da planilha

    Este modelo checa os dados do Google Sheets
    """
    linha: int
    atividade: str
    responsavel_raw: str
    data_inicio: Optional[date]
    data_fim: Optional[date]
    status_raw: str
    project_id: str
    project_man: str

    @field_validator('atividade', 'responsavel_raw')
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Campo não pode vazio")
        return v.strip()
    

class ProcessedActivity(RawActivity):
    """
    Modelo interno para atividade processada

    Adiciona campos calculados como dias de atraso e responsáveis normalizados
    """

    resposaveis: List[str] = Field(description="Lista de responsáveis")
    status_calculado: ActivityStatus = Field(description="Status calculado")
    dias_atraso: int = Field(default= 0)
    email_resposavel: Optional[str] = Field(default=None)


# Mesagens de erro padronizadas

class ErrorResponse(BaseModel):
    """
    Modelo padrão para respostas de erros
    """
    error: str = Field(description="Tipo de erro")
    message: str = Field(description="Mensagem detalhada")
    timestamp: datetime = Field(default_factory=datetime.now)

    # Opcionais para debug
    path: Optional[str] = Field(default= None)
    details: Optional[Dict[str, Any]] = Field(default=None)


# Configuração de Exemplo

examples = {
    "execute_request": {
        "summary": "Executar todos os projetos",
        "value": {
            "project": None,
            "force": True,
            "mode": "production"
        }
    },
    "error_resquest_specfic": {
        "summary": "Executar projeto específico em modo teste",
        "value": {
            "project": "sensor_diabetes",
            "force": False,
            "mode": "test"
        }
    },
    "error_response": {
        "summary": "Erro de configuração",
        "value": {
            "error": "ConfigurationError",
            "message": "Arquivo credenciais.json não encontrado",
            "path": "/execute"
        }
    }
}
