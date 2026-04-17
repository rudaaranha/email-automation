"""Testes unitários para as carregamento das configurações do projeto"""
import os
import pytest


class TestConfig:

    @pytest.mark.unit
    def config_test_email(self, config):
        """Teste do carregamento correto das configurações"""

        assert config.EMAIL_NATS is not None
        assert "@" in config.EMAIL_NATS

    
    @pytest.mark.unit
    def upload_test_spreadsheet(self, config):
        """Teste do carregamento correto das planilhas"""
        assert len(config.SPREADSHEETS) > 0, 'nenhuma planilha configurada'

        for nome, id_ in config.SPREADSHEETS.items():
            assert isinstance(nome, str), f'Nome "{nome}" deve ser string'
            assert isinstance(id_, str), f'ID "{id_}" deve ser string'
            assert len(id_) > 0, f'ID da planilha "{nome}" está vazio'

    
    @pytest.mark.unit
    def json_path_test(self, config):
        """Teste o caminho do JSON está correto"""
        assert os.path.isabs(config.PATH_JSON)
        assert config.PATH_JSON.endswith('credenciais.json')

    @pytest.mark.unit
    def test_worksheet_activities(self, config):
        """Teste para verificar o nome das abas""" 
        assert config.ACTIVITIES_WORKSHEET == "ENTREGA DE ATIVIDADES"
        assert config.RESEARCHERS_WORKSHEET == "PESQUISADORES"

    @pytest.mark.unit
    def test_columns(self, config):
        """Teste para mapeamento das colunas"""
        columns = ['atividade', 'data_inicio', 'data_fim', 'status', 'responsavel']

        for column in columns:
            assert column in config.COLUMNS, f'Coluna "{column}" não encontrada.'

        assert config.COLUMNS['atividade'] == "DEMANDA"
        assert config.COLUMNS['data_inicio'] == "DIA INICIO"
        assert config.COLUMNS['data_fim'] == "DIA DE TÉRMINO"
        assert config.COLUMNS['status'] == "SITUAÇÃO"
        assert config.COLUMNS['responsavel'] == "RESPONSÁVEL"


    @pytest.mark.unit
    def additional_config_tests(self, config):
        """Verificação de outras configurações importantes"""
        
        # Configurações de alerta
        assert config.RESENDING_DAYS_DELAY == 3, f'O reenvio deveria ser 3, mas é {config.RESENDING_DAYS_DELAY}'

        # Execution time
        assert len(config.EXECUTION_HOUR) ==2, f'Deveriam ser 2 horários, mas é/são {config.EXECUTION_HOUR}'
        assert "09:00" in config.EXECUTION_HOUR
        assert "14:00" in config.EXECUTION_HOUR

        # Test mode
        assert isinstance(config.TEST_MODE, bool)


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-m unit', '--tb=short'])
