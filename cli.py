#!/usr/bin/env python
"""
Command Line Interface for the Alert System.

This module allows running the alert system from the terminal
without starting the FastAPI server. Useful for testing and
automated scripts.

Usage:
    python cli.py --once                 # Run once and exit
    python cli.py --test                 # Run in test mode (no real emails)
    python cli.py --project sensor_diabetes  # Run specific project
    python cli.py --once --test --project sensor_diabetes  # Combine options
    python cli.py --schedule             # Run with scheduling (like main.py)
    python cli.py --help                 # Show this help message

Examples:
    # Run all projects in test mode
    python cli.py --once --test

    # Run specific project in production mode
    python cli.py --once --project sensor_diabetes

    # Schedule execution (runs at 9:00 and 14:00)
    python cli.py --schedule
"""

import argparse
import sys
import os
import time
from datetime import datetime

# Add project root to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.alert_system import AlertSystem
from src.config import Config


# ============================================
# HELPER FUNCTIONS
# ============================================

def print_header():
    """Print application header."""
    print("=" * 60)
    print("🚀 Sistema de Alertas de Atividades - CLI")
    print("=" * 60)


def print_result(result: dict):
    """Print execution result in a readable format."""
    print("\n" + "=" * 60)
    print("📊 RESULTADO DA EXECUÇÃO")
    print("=" * 60)
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
        return
    
    print(f"📋 Projetos processados: {result.get('total_spreadsheets', result.get('projects_processed', 0))}")
    print(f"📊 Total de atividades: {result.get('total_activities', 0)}")
    
    alerts = result.get('alerts_sent', {})
    if alerts:
        print("\n📧 Alertas enviados:")
        print(f"   🚀 Início: {alerts.get('start', 0)}")
        print(f"   ⚠️  Atraso: {alerts.get('delay', 0)}")
        print(f"   ✅ Conclusão: {alerts.get('completion', 0)}")
    
    errors = result.get('errors', [])
    if errors:
        print(f"\n❌ Erros ({len(errors)}):")
        for error in errors:
            print(f"   - {error}")
    
    print("\n" + "=" * 60)


# ============================================
# EXECUTION FUNCTIONS
# ============================================

def run_once(test_mode: bool = False, project_name: str = None):
    """
    Run the alert system once and exit.
    
    Args:
        test_mode: If True, run in test mode (no real emails)
        project_name: Specific project to process (None = all projects)
    """
    print_header()
    
    if test_mode:
        print("🧪 Modo TESTE ativado - Nenhum email será enviado")
    else:
        print("📤 Modo PRODUÇÃO ativado - Emails serão enviados")
    
    if project_name:
        print(f"📋 Processando projeto específico: {project_name}")
    else:
        print("📋 Processando TODOS os projetos configurados")
    
    print("-" * 60)
    
    # Configure test mode
    config = Config()
    if test_mode:
        config.TEST_MODE = True
    
    # Create alert system
    system = AlertSystem(config)
    
    # Execute
    start_time = time.time()
    
    if project_name:
        result = system.process_single_project(project_name)
    else:
        result = system.process_all_spreadsheets()
    
    elapsed_time = time.time() - start_time
    
    # Print result
    print_result(result)
    print(f"\n⏱️  Tempo de execução: {elapsed_time:.2f} segundos")
    
    # Return exit code
    if result.get('errors') and len(result.get('errors', [])) > 0:
        return 1
    return 0


def run_schedule():
    """
    Run the alert system with scheduling (like main.py).
    
    This runs continuously and executes at configured hours.
    Press Ctrl+C to stop.
    """
    print_header()
    print("⏰ Modo AGENDAMENTO ativado")
    print("   O sistema executará nos horários configurados:")
    
    config = Config()
    print(f"   Horários: {', '.join(config.EXECUTION_HOUR)}")
    print("-" * 60)
    print("Pressione Ctrl+C para parar")
    print("=" * 60)
    
    system = AlertSystem(config)
    
    # Run once immediately
    print("\n🔄 Executando primeira verificação...")
    system.process_all_spreadsheets()
    
    try:
        import schedule
        
        # Schedule executions
        for hour in config.EXECUTION_HOUR:
            schedule.every().day.at(hour).do(system.process_all_spreadsheets)
            print(f"📅 Agendado para: {hour}")
        
        print("\n⏳ Aguardando próximo horário agendado...")
        print("   (Pressione Ctrl+C para parar)")
        
        while True:
            schedule.run_pending()
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n👋 Sistema encerrado pelo usuário")
        return 0
    except ImportError:
        print("\n❌ Erro: Biblioteca 'schedule' não instalada")
        print("   Execute: pip install schedule")
        return 1


# ============================================
# MAIN ENTRY POINT
# ============================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Sistema de Alertas de Atividades - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python cli.py --once --test
  python cli.py --once --project sensor_diabetes
  python cli.py --schedule
  python cli.py --once --test --project sensor_diabetes
        """
    )
    
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa uma vez e sai"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo teste (não envia emails reais)"
    )
    
    parser.add_argument(
        "--project",
        type=str,
        help="Nome do projeto específico para processar"
    )
    
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Executa com agendamento (modo contínuo)"
    )
    
    args = parser.parse_args()
    
    # Show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    # Execute based on arguments
    if args.schedule:
        return run_schedule()
    elif args.once:
        return run_once(test_mode=args.test, project_name=args.project)
    else:
        # If neither --once nor --schedule, show help
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
