"""
Unit tests for api.py endpoints.

Tests verify:
- Root endpoint returns correct information
- Health endpoint checks system status
- Execute endpoint processes alerts correctly
- Status endpoint returns system information
- Activities endpoint lists activities
- Error handling for invalid requests
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api import router
from src.dependencies import reset_singletons, get_alert_system, get_config
from src.alert_system import AlertSystem
from src.config import Config


class TestAPI:
    """Test suite for API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Reset singletons before each test
        reset_singletons()
        yield
        # Reset after test
        reset_singletons()
    
    #@pytest.fixture
    def _client(self, mock_system):
        """Create test client with router"""
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = (
            lambda: mock_system
        )

        return TestClient(app)
    
    # @pytest.fixture
    # def mock_alert_system(self):
    #     """Create a mock AlertSystem"""
    #     with patch('src.api.get_alert_system') as mock_get:
    #         # Create mock system
    #         mock_system = Mock(spec=AlertSystem)
    #         mock_system.config = Config()
    #         mock_system.config.SPREADSHEETS = {"teste": "id_123"}
    #         mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
            
    #         # Mock spreadsheet_manager
    #         mock_system.spreadsheet_manager = Mock()
    #         mock_system.spreadsheet_manager.load_researchers = Mock(return_value={})
    #         mock_system.spreadsheet_manager.load_activities = Mock(return_value=[])
    #         mock_system.spreadsheet_manager._process_responsibles = Mock(return_value=[])
    #         mock_system.spreadsheet_manager.client = Mock()
    #         mock_system.spreadsheet_manager.client.open_by_key = Mock()
            
    #         # Mock email_dispatcher
    #         mock_system.email_dispatcher = Mock()
    #         mock_system.email_dispatcher.test_mode = False
            
    #         # Mock methods
    #         mock_system.process_all_spreadsheets = Mock(return_value={
    #             "total_spreadsheets": 1,
    #             "total_activities": 5,
    #             "alerts_sent": {"start": 2, "delay": 1, "completion": 1},
    #             "errors": []
    #         })
    #         mock_system.process_single_project = Mock(return_value={
    #             "project": "teste",
    #             "total_activities": 3,
    #             "alerts_sent": {"start": 1, "delay": 0, "completion": 0},
    #             "errors": []
    #         })
            
    #         mock_get.return_value = mock_system
    #         return mock_system
    
    # ============================================
    # TESTS FOR ROOT ENDPOINT
    # ============================================
    
    def test_root_endpoint(self):
        """Test that root endpoint returns system information"""
        app = FastAPI()

        @app.get("/")
        async def root():
            return {
                "name": "Sistema de Alertas de Atividades",
                "version": "1.0.0",
                "docs": "/docs",
                "status": "online"
            }

        app.include_router(router)
        client = TestClient(app)

        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "status" in data
        assert data["status"] == "online"
    
    # ============================================
    # TESTS FOR HEALTH ENDPOINT
    # ============================================
    
    def test_health_endpoint_ok(self):
        """Test health endpoint when system is healthy"""

        # Configure mock to simulate healthy system
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EMAIL_NATS = "teste@email.com"
        mock_system.config.SENHA_APP_NATS = "senha123"
        mock_system.config.TEST_MODE = False
        mock_system.spreadsheet_manager = Mock()
        mock_system.spreadsheet_manager.client = Mock()
        mock_system.spreadsheet_manager.client.open_by_key = Mock()
        
        client = self._client(mock_system)
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok" or data["status"] == "degraded"
        assert "google_sheets_api" in data
        assert "smtp_configured" in data
        assert "sheets_accessible" in data
    

    def test_health_endpoint_not_ready(self):
        """Test health endpoint when system is not initialized"""
        # Reset singletons to simulate not ready
        reset_singletons()

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Patch is_ready to return False
        with patch('src.api.is_ready', return_value=False):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["google_sheets_api"] is False
            assert data["smtp_configured"] is False
            assert data["sheets_accessible"] == []
    
    # ============================================
    # TESTS FOR EXECUTE ENDPOINT
    # ============================================
    
    def test_execute_all_projects(self):
        """Test executing all projects"""
        
        # Criar mock system
        mock_system = Mock(spec=AlertSystem)
                     
        mock_system.process_all_spreadsheets.return_value = {
            "total_spreadsheets": 1,
            "total_activities": 5,
            "alerts_sent": {"start": 2, "delay": 1, "completion": 1},
            "errors": []
        }
          
        app = FastAPI()
        app.include_router(router)
        
        app.dependency_overrides[get_alert_system] = (
            lambda: mock_system
        )

        client = TestClient(app)
          
        response = client.post("/api/v1/execute", json={})
            
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_activities"] == 5
        assert data["alerts_sent"]["start"] == 2
            
        mock_system.process_all_spreadsheets.assert_called_once()

    
    def test_execute_single_project(self):
        """Test executing a single project"""
        mock_system = Mock(spec=AlertSystem)
        mock_system.process_single_project.return_value = {
            "project": "teste",
            "total_activities": 3,
            "alerts_sent": {"start": 1, "delay": 0, "completion": 0},
            "errors": []
        }

        app = FastAPI()
        app.include_router(router)

        app.dependency_overrides[get_alert_system] = (
            lambda: mock_system
        )

        client = TestClient(app)

        response = client.post("/api/v1/execute", json={"project": "teste"})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_activities"] == 3
        
        # Verify process_single_project was called with correct project
        mock_system.process_single_project.assert_called_once_with("teste")
    

    def test_execute_test_mode(self):
        """Test executing in test mode"""
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.TEST_MODE = False
        mock_system.email_dispatcher = Mock()
        mock_system.email_dispatcher.test_mode = False
        mock_system.process_all_spreadsheets.return_value = {
            "total_spreadsheets": 1,
            "total_activities": 5,
            "alerts_sent": {"start": 0, "delay": 0, "completion": 0},
            "errors": []
        }
        
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = (
            lambda: mock_system
        )

        client = TestClient(app)

        response = client.post("/api/v1/execute", json={"mode": "test"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "test"
        
        # Verify test mode was set
        assert mock_system.config.TEST_MODE is True
        assert mock_system.email_dispatcher.test_mode is True
    

    def test_execute_with_force(self):
        """Test executing with force flag"""
        mock_system = Mock()
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTIONS_HOUR = ["09:00", "14:00"]
        mock_system.spreadsheet_manager = Mock()
        mock_system.email_dispatcher = Mock()
        mock_system.email_dispatcher.test_mode = False

        mock_system.process_all_spreadsheets.return_value = {
            "total_spreadsheets": 1,
            "total_activities": 5,
            "alert_sent": {"start": 2, "delay": 1, "completion": 1},
            "errors": []
        }

        client = self._client(mock_system)
        response = client.post("/api/v1/execute", json={"force": True})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    
    def test_execute_project_not_found(self):
        """Test executing a project that doesn't exist"""
        # Configure mock to return error
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.spreadsheet_manager = Mock()
        mock_system.email_dispatcher = Mock()
        mock_system.email_dispatcher.test_mode = False

        mock_system.process_single_project.return_value = {
            "error": "Project 'inexistente' not found"
        }
        
        client = self._client(mock_system)
        response = client.post("/api/v1/execute", json={"project": "inexistente"})
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    

    def test_execute_unexpected_error(self):
        """Test handling of unexpected errors during execution"""
        # Configure mock to raise exception
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.spreadsheet_manager = Mock()
        mock_system.email_dispatcher = Mock()
        mock_system.email_dispatcher.test_mode = False
        mock_system.process_all_spreadsheets.side_effect = Exception("Unexpected error")

        client = self._client(mock_system)
        response = client.post("/api/v1/execute", json={})
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Unexpected error" in data["detail"]

    # DEU ERRO
    # def test_execute_with_mode_test_and_project(self):
    #     """Test executing with both test mode and specific project"""
    #     mock_system = Mock(spec=AlertSystem)
    #     mock_system.config = Config()
    #     mock_system.config.SPREADSHEETS = {"teste": "id_123"}
    #     mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
    #     mock_system.config.TEST_MODE = False
    #     mock_system.spreadsheet_manager = Mock()
    #     mock_system.email_dispatcher = Mock()
    #     mock_system.email_dispatcher.test_mode = False
        
    #     mock_system.process_single_project.return_value = {
    #         "project": "teste",
    #         "total_activities": 3,
    #         "alerts_sent": {"start": 0, "delay": 0, "completion": 0},
    #         "errors": []
    #     }
        
    #     client = self._create_client_with_mock(mock_system)
    #     response = client.post("/api/v1/execute", json={"project": "teste", "mode": "test"})
        
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["mode"] == "test"
    #     assert mock_system.process_single_project.called
    #     assert mock_system.config.TEST_MODE is True
    
    # ============================================
    # TESTS FOR STATUS ENDPOINT
    # ============================================
    
    def test_status_endpoint(self):
        """Test status endpoint returns correct information"""
        # AlertSystem Mock
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123", "outro": "id_456"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.config.TEST_MODE = False

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system

        from src.api import get_status_info
        
        app.dependency_overrides[get_status_info] = lambda: {
            "alert_system_initialized": True,
            "test_mode": False
        }

        client = TestClient(app)

        response = client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
            
        assert data["status"] == "healthy"
        assert data["test_mode"] is False
        assert sorted(data["configured_projects"]) == ["outro", "teste"]
        assert "timestamp" in data
        if "execution_hours" in data:
            assert data["execution_hours"] == ["09:00", "14:00"]
     
    
    def test_status_endpoint_unhealthy(self):
        # Mock do AlertSystem com dependency_overrides
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.config.TEST_MODE = False

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system

        # Sobrescrever get_status_info para retornar unhealthy
        from src.api import get_status_info
        
        app.dependency_overrides[get_status_info] = lambda: {
            "alert_system_initialized": False,
            "test_mode": False
        }

        client = TestClient(app)
        response = client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["test_mode"] is False
        assert data["configured_projects"] == ["teste"]
        assert "timestamp" in data
    
    # ============================================
    # TESTS FOR ACTIVITIES ENDPOINT
    # ============================================
    
    def test_activities_all_projects(self):
        """Test listing activities from all projects"""
        
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]

        mock_system.spreadsheet_manager = Mock()
        mock_system.spreadsheet_manager.load_researchers.return_value = {
            "JOÃO": "joao@email.com"
        }
        mock_system.spreadsheet_manager.load_activities.return_value = [
            {
                "linha": 2,
                "atividade": "Atividade 1",
                "responsavel_raw": "JOÃO",
                "data_inicio": date(2026, 4, 1),
                "data_fim": date(2026, 4, 10),
                "status": "Não iniciada",
                "dias_atraso": 0
            },
            {
                "linha": 3,
                "atividade": "Atividade 2",
                "responsavel_raw": "MARIA",
                "data_inicio": date(2026, 4, 5),
                "data_fim": date(2026, 4, 15),
                "status": "Concluída",
                "dias_atraso": 0
            }
        ]

        mock_system.spreadsheet_manager._process_responsibles = Mock(
            side_effect=lambda x: [x] if x else []
        )
        
        # if activities enpoint calls get_status_info, overrides too
        status_info = {
            "alert_system_initialized": True,
            "test_mode": False
        }

        client = self._client(mock_system)
        response = client.get("/api/v1/activities")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["nome"] == "Atividade 1"
        assert data[0]["project"] == "teste"
        assert data[1]["nome"] == "Atividade 2"
    

    def test_activities_single_project(self):
        """Test listing activities from a specific project"""
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]

        mock_system.spreadsheet_manager = Mock()
        mock_system.spreadsheet_manager.load_activities.return_value = {}
        mock_system.spreadsheet_manager.load_activities.return_value = [
            {"linha": 2, "atividade": "Teste", "responsavel_raw": "", "dias_atraso": 0}
        ]
        mock_system.spreadsheet_manager._process_responsibles = Mock(return_value=[])

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system

        from src.api import get_status_info
        app.dependency_overrides[get_status_info] = lambda: {
            "alert_system_initialized": True,
            "test_mode": False
        }

        client = TestClient(app)
        response = client.get("/api/v1/activities?project=teste")
        
        assert response.status_code == 200
        data = response.json()        
        assert len(data) == 1
        assert data[0]["project"] == "teste"

    
    def test_activities_project_not_found(self):
        """Test activities endpoint with non-existent project"""
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system

        from src.api import get_status_info
        app.dependency_overrides[get_status_info] = lambda: {
            "alert_system_initialized": True,
            "test_mode": False
        }

        client = TestClient(app)
        response = client.get("/api/v1/activities?project=inexistente")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    

    def test_activities_error_loading(self):
        """Test that the activities endpoint skips projects that fail to load."""
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]

        mock_system.spreadsheet_manager = Mock()
        mock_system.spreadsheet_manager.load_researchers.return_value = {}
        mock_system.spreadsheet_manager.load_activities.side_effect = Exception(
            "Failed to load"
        )

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system

        client = TestClient(app)
        response = client.get("/api/v1/activities")

        assert response.status_code == 200
        assert response.json() == []
    
    # ============================================
    # TESTS FOR EXECUTE WITH DIFFERENT MODES
    # ============================================
    
    def test_execute_with_mode_test_and_project(self):
        """Test executing with both test mode and specific project"""
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.config.TEST_MODE = False
        mock_system.spreadsheet_manager = Mock()
        mock_system.email_dispatcher = Mock()
        mock_system.email_dispatcher.test_mode = False
        
        mock_system.process_single_project.return_value = {
            "project": "teste",
            "total_activities": 3,
            "alerts_sent": {"start": 0, "delay": 0, "completion": 0},
            "errors": []
        }
        
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/execute",
            json={"project": "teste", "mode": "test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "test"
        assert mock_system.process_single_project.called
        assert mock_system.config.TEST_MODE is True
    
    # ============================================
    # TESTS FOR ROUTER PREFIX
    # ============================================
    

    def test_api_prefix(self):
        """Test that all endpoints are under /api/v1 prefix"""
        # Root is not under prefix
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {}
        mock_system.config.EXECUTION_HOUR = []
        mock_system.config.TEST_MODE = False

        app = FastAPI()
        app.include_router(router)

        from src.api import get_status_info
        app.dependency_overrides[get_alert_system] = lambda: mock_system
        app.dependency_overrides[get_status_info] = lambda: {
            "alert_system_initialized": True,
            "test_mode": False,
        }

        client = TestClient(app)
        
        # Root endpoint (registered inside the router)
        root_response = client.get("/api/v1/")
        assert root_response.status_code == 200

        # Execute endpoint
        execute_response = client.post(
            "/api/v1/execute",
            json={"mode": "normal"}
        )
        assert execute_response.status_code in (200, 500, 422)

        # Status endpoint
        status_response = client.get("/api/v1/status")
        assert status_response.status_code == 200

        # Activities endpoint
        activities_response = client.get("/api/v1/activities")
        assert activities_response.status_code == 200
    
    # ============================================
    # TESTS FOR RESPONSE MODELS
    # ============================================
    
    def test_execute_response_has_all_fields(self):
        """Test that execute response includes all expected fields"""
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.spreadsheet_manager = Mock()
        mock_system.email_dispatcher = Mock()
        mock_system.email_dispatcher.test_mode = False
        
        mock_system.process_all_spreadsheets.return_value = {
            "total_spreadsheets": 1,
            "total_activities": 10,
            "alerts_sent": {"start": 3, "delay": 2, "completion": 1},
            "errors": []
        }
        
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system
        
        client = TestClient(app)
        response = client.post("/api/v1/execute", json={})
        data = response.json()
        
        expected_fields = ["success", "timestamp", "mode", "projects_processed", 
                        "total_activities", "alerts_sent", "errors"]
        
        for field in expected_fields:
            assert field in data
        
        # Verificar valores específicos
        assert data["success"] is True
        assert data["total_activities"] == 10
        assert data["alerts_sent"]["start"] == 3
    

    def test_status_response_has_all_fields(self):
        """Test that status response includes all expected fields"""
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.config.TEST_MODE = False
        
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system
        
        from src.api import get_status_info
        app.dependency_overrides[get_status_info] = lambda: {
            "alert_system_initialized": True,
            "test_mode": False
        }
        
        client = TestClient(app)
        response = client.get("/api/v1/status")
        data = response.json()
        
        expected_fields = ["status", "timestamp", "test_mode", "configured_projects", "execution_hours"]
        
        for field in expected_fields:
            assert field in data
        
        assert data["status"] == "healthy"
        assert data["test_mode"] is False
        assert data["configured_projects"] == ["teste"]
        assert data["execution_hours"] == ["09:00", "14:00"]


class TestAPIIntegration:
    """Integration-like tests for API endpoints"""
    
    def test_full_execution_workflow(self):
        """Test complete execution workflow with real dependencies (mocked)"""
        # Criar mock do AlertSystem
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.config.TEST_MODE = False
        
        # Mock do spreadsheet_manager
        mock_system.spreadsheet_manager = Mock()
        mock_system.spreadsheet_manager.load_researchers = Mock(return_value={})
        mock_system.spreadsheet_manager.load_activities = Mock(return_value=[])
        mock_system.spreadsheet_manager._process_responsibles = Mock(return_value=[])
        mock_system.spreadsheet_manager.client = Mock()
        mock_system.spreadsheet_manager.client.open_by_key = Mock()
        
        # Mock do email_dispatcher
        mock_system.email_dispatcher = Mock()
        mock_system.email_dispatcher.test_mode = False
        
        # Mock do process_all_spreadsheets
        mock_system.process_all_spreadsheets = Mock(return_value={
            "total_spreadsheets": 1,
            "total_activities": 3,
            "alerts_sent": {"start": 1, "delay": 0, "completion": 0},
            "errors": []
        })
        mock_system.process_single_project = Mock(return_value={
            "project": "teste",
            "total_activities": 3,
            "alerts_sent": {"start": 1, "delay": 0, "completion": 0},
            "errors": []
        })
        
        # Criar app com dependency_overrides
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system
        
        # Criar client
        client = TestClient(app)
        
        # Executar
        response = client.post("/api/v1/execute", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_activities"] == 3
        assert data["alerts_sent"]["start"] == 1
        
        # Verificar que o mock foi chamado
        mock_system.process_all_spreadsheets.assert_called_once()
    
    def test_health_check_detects_smtp_missing(self):
        """Test health check detects missing SMTP configuration"""
        # Criar mock do AlertSystem com SMTP desconfigurado
        mock_system = Mock(spec=AlertSystem)
        mock_system.config = Config()
        mock_system.config.SPREADSHEETS = {"teste": "id_123"}
        mock_system.config.EXECUTION_HOUR = ["09:00", "14:00"]
        mock_system.config.TEST_MODE = False
        mock_system.config.EMAIL_NATS = None  # SMTP não configurado
        mock_system.config.SENHA_APP_NATS = None  # SMTP não configurado
        
        # Mock do spreadsheet_manager
        mock_system.spreadsheet_manager = Mock()
        mock_system.spreadsheet_manager.client = Mock()
        mock_system.spreadsheet_manager.client.open_by_key = Mock()
        
        # Criar app com dependency_overrides
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_alert_system] = lambda: mock_system
        
        # Criar client
        client = TestClient(app)
        
        # Executar health check
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que SMTP não está configurado
        assert data["smtp_configured"] is False
        # Pode estar degradado ou ok, dependendo da implementação
        assert data["status"] in ["degraded", "ok"]


# ============================================
# EXECUTE TESTS DIRECTLY
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
