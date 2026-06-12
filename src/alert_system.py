"""
Alert System - Core orchestration module.

This module is the brain of the system. It coordinates:
- Reading spreadsheets via SpreadsheetManager
- Reading researchers via SpreadsheetManager
- Deciding which alerts to send for each activity
- Sending alerts via EmailDispatcher
- Tracking what was sent
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from src.config import Config
from src.spreadsheet_manager import SpreadsheetManager
from src.email_dispatcher import EmailDispatcher


class AlertSystem:
    """
    Core orchestration class for the alert system.
    
    This class coordinates all components to:
    1. Load researchers and activities from Google Sheets
    2. Analyze each activity to determine which alerts are needed
    3. Send appropriate alerts via email
    4. Return statistics about the execution
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the AlertSystem with configuration.
        
        Args:
            config: Configuration object. If None, creates a new Config instance.
        """
        self.config = config or Config()
        self.spreadsheet_manager = SpreadsheetManager(self.config)
        self.email_dispatcher = EmailDispatcher(self.config)
        
        # Statistics tracking
        self.stats = {
            "total_spreadsheets": 0,
            "total_activities": 0,
            "alerts_start": 0,
            "alerts_delay": 0,
            "alerts_completion": 0,
            "errors": []
        }
    
    def process_all_spreadsheets(self) -> Dict[str, Any]:
        """
        Process all spreadsheets configured in SPREADSHEETS.
        
        Returns:
            Dictionary with execution statistics
        """
        print("\n" + "="*60)
        print("🚀 STARTING ALERT SYSTEM EXECUTION")
        print("="*60)
        
        # Reset statistics
        self._reset_stats()
        
        # Process each spreadsheet
        for project_name, spreadsheet_id in self.config.SPREADSHEETS.items():
            if not spreadsheet_id:
                print(f"⚠️ No ID for project: {project_name}")
                continue
            
            print(f"\n📋 Processing project: {project_name.upper()}")
            self._process_single_spreadsheet(spreadsheet_id, project_name)
            self.stats["total_spreadsheets"] += 1
        
        # Print final summary
        self._print_summary()
        
        return {
            "total_spreadsheets": self.stats["total_spreadsheets"],
            "total_activities": self.stats["total_activities"],
            "alerts_sent": {
                "start": self.stats["alerts_start"],
                "delay": self.stats["alerts_delay"],
                "completion": self.stats["alerts_completion"]
            },
            "errors": self.stats["errors"]
        }
    
    def _reset_stats(self):
        """Reset all statistics counters."""
        self.stats = {
            "total_spreadsheets": 0,
            "total_activities": 0,
            "alerts_start": 0,
            "alerts_delay": 0,
            "alerts_completion": 0,
            "errors": []
        }
    
    def _process_single_spreadsheet(self, spreadsheet_id: str, project_name: str):
        """
        Process a single spreadsheet.
        
        Args:
            spreadsheet_id: Google Sheets ID
            project_name: Name of the project (for logging)
        """
        today = datetime.now().date()
        
        # Step 1: Load researchers
        try:
            researchers = self.spreadsheet_manager.load_researchers(spreadsheet_id)
            print(f"   📧 Loaded {len(researchers)} researchers")
        except Exception as e:
            error_msg = f"Failed to load researchers for {project_name}: {e}"
            print(f"   ❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return
        
        # Step 2: Load activities
        try:
            activities = self.spreadsheet_manager.load_activities(spreadsheet_id)
            print(f"   📊 Loaded {len(activities)} activities")
            self.stats["total_activities"] += len(activities)
        except Exception as e:
            error_msg = f"Failed to load activities for {project_name}: {e}"
            print(f"   ❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return
        
        # Step 3: Process each activity
        for activity in activities:
            self._process_activity(activity, researchers, project_name, today)
    
    def _process_activity(self, activity: Dict[str, Any], 
                          researchers: Dict[str, str],
                          project_name: str, 
                          today: date):
        """
        Process a single activity and send appropriate alerts.
        
        Args:
            activity: Activity dictionary from spreadsheet_manager
            researchers: Dictionary mapping names to emails
            project_name: Name of the project
            today: Current date for comparison
        """
        activity_name = activity.get("atividade", "Unknown")
        status = activity.get("status", "")
        start_date = activity.get("data_inicio")
        end_date = activity.get("data_fim")
        responsible_raw = activity.get("responsavel_raw", "")
        
        # Skip activities without a name
        if not activity_name:
            return
        
        # Process multiple responsibilities
        responsible_names = self.spreadsheet_manager._process_responsibles(responsible_raw)
        
        if not responsible_names:
            print(f"   ⚠️ No responsible for activity: {activity_name}")
            return
        
        # Find emails for each responsible
        responsible_emails = []
        for name in responsible_names:
            email = researchers.get(name)
            if email:
                responsible_emails.append((name, email))
            else:
                print(f"   ⚠️ No email found for: {name} (activity: {activity_name})")
        
        if not responsible_emails:
            return
        
        # Check for COMPLETION alert (status changed to "Concluídas")
        # Note: In a real system, you'd track previous status
        # For now, we just check if current status is "Concluídas"
        if status == "Concluídas":
            self._send_completion_alerts(responsible_emails, activity_name, project_name)
        
        # Check for START alert (start_date == today)
        elif start_date and start_date == today:
            end_date_str = end_date.strftime("%d/%m/%Y") if end_date else "N/A"
            start_date_str = start_date.strftime("%d/%m/%Y")
            
            self._send_start_alerts(
                responsible_emails, activity_name, 
                start_date_str, end_date_str, project_name
            )
        
        # Check for DELAY alert (end_date < today and not completed)
        elif end_date and end_date < today and status != "Concluídas":
            days_delayed = (today - end_date).days
            end_date_str = end_date.strftime("%d/%m/%Y")
            
            self._send_delay_alerts(
                responsible_emails, activity_name,
                end_date_str, days_delayed, project_name
            )
    
    def _send_start_alerts(self, recipients: List[Tuple[str, str]], 
                           activity_name: str, start_date: str,
                           end_date: str, project_name: str):
        """
        Send start alerts to all recipients.
        
        Args:
            recipients: List of (name, email) tuples
            activity_name: Name of the activity
            start_date: Formatted start date
            end_date: Formatted end date
            project_name: Name of the project
        """
        for name, email in recipients:
            success = self.email_dispatcher.send_alert_start(
                to_email=email,
                responsible_name=name,
                activity_name=activity_name,
                start_date=start_date,
                end_date=end_date,
                project_name=project_name
            )
            
            if success:
                self.stats["alerts_start"] += 1
                print(f"   ✅ Start alert sent to: {name} ({email})")
            else:
                error_msg = f"Failed to send start alert to {email} for {activity_name}"
                self.stats["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
    
    def _send_delay_alerts(self, recipients: List[Tuple[str, str]],
                           activity_name: str, end_date: str,
                           days_delayed: int, project_name: str):
        """
        Send delay alerts to all recipients.
        
        Args:
            recipients: List of (name, email) tuples
            activity_name: Name of the activity
            end_date: Formatted end date
            days_delayed: Number of days delayed
            project_name: Name of the project
        """
        for name, email in recipients:
            success = self.email_dispatcher.send_alert_delay(
                to_email=email,
                responsible_name=name,
                activity_name=activity_name,
                end_date=end_date,
                days_delayed=days_delayed,
                project_name=project_name
            )
            
            if success:
                self.stats["alerts_delay"] += 1
                print(f"   ⚠️ Delay alert sent to: {name} ({email}) - {days_delayed} days")
            else:
                error_msg = f"Failed to send delay alert to {email} for {activity_name}"
                self.stats["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
    
    def _send_completion_alerts(self, recipients: List[Tuple[str, str]],
                                activity_name: str, project_name: str):
        """
        Send completion alerts to all recipients.
        
        Args:
            recipients: List of (name, email) tuples
            activity_name: Name of the activity
            project_name: Name of the project
        """
        for name, email in recipients:
            success = self.email_dispatcher.send_alert_completion(
                to_email=email,
                responsible_name=name,
                activity_name=activity_name,
                project_name=project_name
            )
            
            if success:
                self.stats["alerts_completion"] += 1
                print(f"   ✅ Completion alert sent to: {name} ({email})")
            else:
                error_msg = f"Failed to send completion alert to {email} for {activity_name}"
                self.stats["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
    
    def _print_summary(self):
        """Print execution summary."""
        print("\n" + "="*60)
        print("📊 EXECUTION SUMMARY")
        print("="*60)
        print(f"   Spreadsheets processed: {self.stats['total_spreadsheets']}")
        print(f"   Total activities: {self.stats['total_activities']}")
        print(f"   Start alerts sent: {self.stats['alerts_start']}")
        print(f"   Delay alerts sent: {self.stats['alerts_delay']}")
        print(f"   Completion alerts sent: {self.stats['alerts_completion']}")
        print(f"   Errors: {len(self.stats['errors'])}")
        print("="*60)
    
    def process_single_project(self, project_name: str) -> Dict[str, Any]:
        """
        Process a single project by name.
        
        Args:
            project_name: Name of the project (key in SPREADSHEETS)
            
        Returns:
            Dictionary with execution statistics
        """
        if project_name not in self.config.SPREADSHEETS:
            error_msg = f"Project '{project_name}' not found in configuration"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
        
        spreadsheet_id = self.config.SPREADSHEETS[project_name]
        
        # Reset statistics
        self._reset_stats()
        
        print("\n" + "="*60)
        print(f"🚀 STARTING SINGLE PROJECT: {project_name.upper()}")
        print("="*60)
        
        self._process_single_spreadsheet(spreadsheet_id, project_name)
        self._print_summary()
        
        return {
            "project": project_name,
            "total_activities": self.stats["total_activities"],
            "alerts_sent": {
                "start": self.stats["alerts_start"],
                "delay": self.stats["alerts_delay"],
                "completion": self.stats["alerts_completion"]
            },
            "errors": self.stats["errors"]
        }
