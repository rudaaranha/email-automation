"""
"banco de templates" que contém apenas os textos HTML dos emails. Ele não envia emails, não tem lógica de negócio, 
não acessa banco de dados. Só devolve strings HTML prontas para serem enviadas.
"""

from datetime import datetime
from typing import List, Dict, Any

class EmailTemplates:
    """HTML email templates for different alert types"""

    @staticmethod
    def alert_start(responsible_name: str, activity_name: str, start_date: str, end_date: str, project_name: str) -> str:
        """
        Template for activity start alert
        
        Args:
            responsible_name: Name of the person responsible
            activity_name: Name of the activity
            start_date: Formatted start date (DD/MM/YYYY)
            end_date: Formatted end date (DD/MM/YYYY)
            project_name: Name of the project
        
        Returns:
            HTML string for the email
        """
        return f""""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                
                <!-- Cabeçalho -->
                <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; color: white;">📋 Iniciar Atividade</h2>
                </div>
                
                <!-- Conteúdo -->
                <div style="padding: 30px;">
                    
                    <!-- Saudação -->
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                        Olá <strong>{responsible_name}</strong>,
                    </p>
                    
                    <!-- Mensagem principal -->
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                        Esta é uma notificação automática informando que a atividade abaixo deve ser 
                        <strong style="color: #3498db;">INICIADA HOJE</strong>:
                    </p>
                    
                    <!-- Bloco de informações -->
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
                        <p style="margin: 5px 0;"><strong>📌 Projeto:</strong> {project_name}</p>
                        <p style="margin: 5px 0;"><strong>📝 Atividade:</strong> {activity_name}</p>
                        <p style="margin: 5px 0;"><strong>📅 Data de Início:</strong> {start_date}</p>
                        <p style="margin: 5px 0;"><strong>🎯 Data de Entrega:</strong> {end_date}</p>
                    </div>
                    
                    <!-- Aviso -->
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0; color: #856404;">
                            ⚠️ <strong>Importante:</strong> Por favor, inicie esta atividade o quanto antes para garantir a entrega no prazo.
                        </p>
                    </div>
                    
                    <!-- Linha divisória -->
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                    
                    <!-- Rodapé -->
                    <p style="color: #7f8c8d; font-size: 12px; margin: 0; text-align: center;">
                        Este é um email automático do sistema de gerenciamento de projetos.<br>
                        Por favor, não responda a esta mensagem.
                    </p>
                    
                </div>
            </div>
        </body>
        </html>
    """
    
    @staticmethod
    def alert_delay(responsible_name: str, activity_name: str,
                    end_date: str, days_delayed: int,
                    project_name: str) -> str:
        """
        Template for activity delay alert
        
        Args:
            responsible_name: Name of the person responsible
            activity_name: Name of the activity
            end_date: Formatted end date (DD/MM/YYYY)
            days_delayed: Number of days delayed
            project_name: Name of the project
        
        Returns:
            HTML string for the email
        """
        # Define cor baseada nos dias de atraso
        if days_delayed > 5:
            header_color = "#c0392b"  # vermelho mais escuro para muito atraso
            alert_color = "#e74c3c"
        else:
            header_color = "#e74c3c"  # vermelho padrão
            alert_color = "#e74c3c"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                
                <!-- Cabeçalho -->
                <div style="background-color: {header_color}; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; color: white;">⚠️ ATENÇÃO: Atividade Atrasada</h2>
                </div>
                
                <!-- Conteúdo -->
                <div style="padding: 30px;">
                    
                    <!-- Saudação -->
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                        Olá <strong>{responsible_name}</strong>,
                    </p>
                    
                    <!-- Mensagem principal -->
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                        Esta é uma notificação automática informando que a atividade abaixo está 
                        <strong style="color: {alert_color};">ATRASADA</strong>:
                    </p>
                    
                    <!-- Bloco de informações -->
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {alert_color};">
                        <p style="margin: 5px 0;"><strong>📌 Projeto:</strong> {project_name}</p>
                        <p style="margin: 5px 0;"><strong>📝 Atividade:</strong> {activity_name}</p>
                        <p style="margin: 5px 0;"><strong>📅 Data de Entrega:</strong> {end_date}</p>
                        <p style="margin: 5px 0;"><strong style="color: {alert_color};">⏰ Dias em Atraso:</strong> {days_delayed} dias</p>
                    </div>
                    
                    <!-- Aviso de urgência -->
                    <div style="background-color: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0; color: #721c24;">
                            🚨 <strong>Urgente!</strong> Por favor, regularize a entrega desta atividade imediatamente.
                        </p>
                    </div>
                    
                    <!-- Linha divisória -->
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                    
                    <!-- Rodapé -->
                    <p style="color: #7f8c8d; font-size: 12px; margin: 0; text-align: center;">
                        Este é um email automático do sistema de gerenciamento de projetos.<br>
                        Por favor, não responda a esta mensagem.
                    </p>
                    
                </div>
            </div>
        </body>
        </html>
    """
    
    @staticmethod
    def alert_completion(responsible_name: str, activity_name: str,
                         project_name: str) -> str:
        """
        Template for activity completion alert
        
        Args:
            responsible_name: Name of the person responsible
            activity_name: Name of the activity
            project_name: Name of the project
        
        Returns:
            HTML string for the email
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                
                <!-- Cabeçalho -->
                <div style="background-color: #27ae60; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; color: white;">✅ Atividade Concluída</h2>
                </div>
                
                <!-- Conteúdo -->
                <div style="padding: 30px;">
                    
                    <!-- Saudação -->
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                        Olá <strong>{responsible_name}</strong>,
                    </p>
                    
                    <!-- Mensagem principal -->
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                        Parabéns! A atividade abaixo foi 
                        <strong style="color: #27ae60;">CONCLUÍDA COM SUCESSO</strong>:
                    </p>
                    
                    <!-- Bloco de informações -->
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #27ae60;">
                        <p style="margin: 5px 0;"><strong>📌 Projeto:</strong> {project_name}</p>
                        <p style="margin: 5px 0;"><strong>📝 Atividade:</strong> {activity_name}</p>
                    </div>
                    
                    <!-- Mensagem de incentivo -->
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0; color: #155724;">
                            🎉 <strong>Excelente trabalho!</strong> Continue assim!
                        </p>
                    </div>
                    
                    <!-- Linha divisória -->
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                    
                    <!-- Rodapé -->
                    <p style="color: #7f8c8d; font-size: 12px; margin: 0; text-align: center;">
                        Este é um email automático do sistema de gerenciamento de projetos.<br>
                        Por favor, não responda a esta mensagem.
                    </p>
                    
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def daily_report(activities_to_start: List[Dict[str, Any]], 
                     activities_delayed: List[Dict[str, Any]],
                     project_name: str) -> str:
        """
        Template for daily report email
        
        Args:
            activities_to_start: List of activities that start today
            activities_delayed: List of delayed activities
            project_name: Name of the project
        
        Returns:
            HTML string for the email
        """
        # Data atual formatada
        today_date = datetime.now().strftime("%d/%m/%Y")
        
        # Construir seção de atividades para iniciar
        start_section = ""
        if activities_to_start:
            start_section = """
                <h3 style="color: #3498db; margin-top: 20px;">📌 Atividades para Iniciar Hoje:</h3>
                <ul style="margin: 10px 0 20px 20px; padding: 0;">
            """
            for act in activities_to_start:
                activity_name = act.get('atividade', act.get('activity_name', 'Sem nome'))
                end_date = act.get('data_fim', act.get('end_date', 'N/A'))
                start_section += f"<li style=\"margin: 8px 0;\"><strong>{activity_name}</strong> - Entrega: {end_date}</li>"
            start_section += "</ul>"
        else:
            start_section = """
                <div style="background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #155724;">✅ Nenhuma atividade para iniciar hoje!</p>
                </div>
            """
        
        # Construir seção de atividades atrasadas
        delay_section = ""
        if activities_delayed:
            delay_section = """
                <h3 style="color: #e74c3c; margin-top: 20px;">⚠️ Atividades Atrasadas:</h3>
                <ul style="margin: 10px 0 20px 20px; padding: 0;">
            """
            for act in activities_delayed:
                activity_name = act.get('atividade', act.get('activity_name', 'Sem nome'))
                days = act.get('dias_atraso', act.get('days_delayed', 0))
                delay_section += f"<li style=\"margin: 8px 0;\"><strong>{activity_name}</strong> - Atraso: {days} dias</li>"
            delay_section += "</ul>"
        else:
            delay_section = """
                <div style="background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #155724;">🎉 Nenhuma atividade atrasada!</p>
                </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                
                <!-- Cabeçalho -->
                <div style="background-color: #2c3e50; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; color: white;">📊 Relatório Diário de Atividades</h2>
                </div>
                
                <!-- Conteúdo -->
                <div style="padding: 30px;">
                    
                    <!-- Informações do relatório -->
                    <p style="font-size: 14px; color: #7f8c8d; margin-bottom: 5px;">
                        <strong>Projeto:</strong> {project_name}
                    </p>
                    <p style="font-size: 14px; color: #7f8c8d; margin-bottom: 20px;">
                        <strong>Data:</strong> {today_date}
                    </p>
                    
                    <!-- Linha divisória -->
                    <hr style="margin: 10px 0 20px 0; border: none; border-top: 1px solid #eee;">
                    
                    {start_section}
                    
                    {delay_section}
                    
                    <!-- Linha divisória -->
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                    
                    <!-- Rodapé -->
                    <p style="color: #7f8c8d; font-size: 12px; margin: 0; text-align: center;">
                        Relatório automático gerado pelo sistema de gerenciamento de projetos.
                    </p>
                    
                </div>
            </div>
        </body>
        </html>
        """
