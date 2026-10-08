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
from src.system_repository import SystemRepository
from src.models import AlertHistory, AlertType, ProjectState


class AlertSystem:
    """
    Core orchestration class for the alert system.
    
    This class coordinates all components to:
    1. Load researchers and activities from Google Sheets
    2. Analyze each activity to determine which alerts are needed
    3. Send appropriate alerts via email
    4. Return statistics about the execution
    """
    
    def __init__(self, 
                config: Optional[Config] = None,
                system_repository: Optional[SystemRepository] = None, 
    ):
        """
        Initialize the AlertSystem with configuration.
        
        Args:
            config: Configuration object. If None, creates a new Config instance.
        """
        self.config = config or Config()
        self.spreadsheet_manager = SpreadsheetManager(self.config)
        self.email_dispatcher = EmailDispatcher(self.config)
        self.system_repository = (
            system_repository
            or SystemRepository(self.config)
        )
        
        # Statistics tracking
        self.stats = {
            "total_spreadsheets": 0,
            "total_activities": 0,
            "alerts_start": 0,
            "alerts_delay": 0,
            "alerts_completion": 0,
            "alerts_3_days": 0,
            "alerts_1_day": 0,
            "errors": []
        }
    
    def process_all_spreadsheets(self) -> Dict[str, Any]:
        """
        Process all active projects configured in the control spreadsheet.

        Only projects with active=True are processed.
        Inactive projects are completely ignored.
        """
        print("\n" + "="*60)
        print("🚀 STARTING ALERT SYSTEM EXECUTION")
        print("=" * 60)
        
        # Reset statistics
        self._reset_stats()

        # Ensure control worksheets exist
        self.system_repository.ensure_control_worksheets()

        # Load only active projects from the control spreadsheet
        active_projects = self.system_repository.get_active_projects()

        print(
            f"\n📋 Active projects found: {len(active_projects)}"
        )

        
        # Process each active project
        for project_state in active_projects:
            project_name = project_state.project
            spreadsheet_id = project_state.spreadsheet_id

            print(
                f"\n📋 Processing project: "
                f"{project_name.upper()}" 
            )

            self._process_single_spreadsheet(
                spreadsheet_id,
                project_name,
            )

            self.stats["total_spreadsheets"] += 1

        # Print final summary
        self._print_summary()

        return{
            "total_spreadsheets": self.stats["total_spreadsheets"],
            "total_activities": self.stats["total_activities"],
            "alerts_sent": {
                "start": self.stats["alerts_start"],
                "delay": self.stats["alerts_delay"],
                "completion": self.stats["alerts_completion"],
                "3_days": self.stats["alerts_3_days"],
                "1_day": self.stats["alerts_1_day"],
            },
            "errors": self.stats["errors"],
        }

    
    def _reset_stats(self):
        """Reset all statistics counters."""
        self.stats = {
            "total_spreadsheets": 0,
            "total_activities": 0,
            "alerts_start": 0,
            "alerts_delay": 0,
            "alerts_completion": 0,
            "alerts_3_days": 0,
            "alerts_1_day": 0,
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

    
    def _process_activity(
            self, 
            activity: Dict[str, Any], 
            researchers: Dict[str, str],
            project_name: str, 
            today: date
    ):
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
                print(
                    f"   ⚠️ No email found for: ) "
                    f"{name} (activity: {activity_name}"
            )
        
        if not responsible_emails:
            return
        
        # Check for COMPLETION alert (status changed to "Concluída")
        # Note: In a real system, you'd track previous status
        # For now, we just check if current status is "Concluída"
        if status == "Concluída":
            self._send_completion_alerts(
                responsible_emails, 
                activity_name, 
                project_name,
            )
        
        # Check for START alert (start_date == today)
        elif start_date and start_date == today:
            end_date_str = (
                end_date.strftime("%d/%m/%Y")
                if end_date
                else "N/A"
            )
            
            start_date_str = start_date.strftime("%d/%m/%Y")
            
            self._send_start_alerts(
                responsible_emails, 
                activity_name, 
                start_date_str, 
                end_date_str, 
                project_name,
            )

        # Check for DEADLINE REMINDER - 3 DAYS
        elif end_date:
            days_until_end = (end_date - today).days

            if days_until_end == 3:
                end_date_str = end_date.strftime("%d/%m/%Y")

                self._send_3_days_alerts(
                    responsible_emails,
                    activity_name,
                    end_date_str,
                    project_name,
                    today,
                )

            elif days_until_end == 1:
                end_date_str = end_date.strftime("%d/%m/%Y")

                self._send_1_day_alerts(
                    responsible_emails,
                    activity_name,
                    end_date_str,
                    project_name,
                    today,
                )

            # Check for DELAY alert
            elif days_until_end < 0:
                days_delayed = abs(days_until_end)
                end_date_str = end_date.strftime("%d/%m/%Y")

                self._send_delay_alerts(
                    responsible_emails,
                    activity_name,
                    end_date_str,
                    days_delayed,
                    project_name,
                    today,
                )

   
    def _send_start_alerts(
            self, 
            recipients: List[Tuple[str, str]], 
            activity_name: str, 
            start_date: str,
            end_date: str, 
            project_name: str,
    ):
        """
        Send start alerts to all recipients.
        The alert is sent only once per project/activity/researcher

        Args:
            recipients: List of (name, email) tuples
            activity_name: Name of the activity
            start_date: Formatted start date
            end_date: Formatted end date
            project_name: Name of the project
        """
        for name, email in recipients:

            #Check whether the start alert was already sent
            already_sent = self.system_repository.alert_was_sent(
                project=project_name,
                activity=activity_name,
                researcher=name,
                alert_type=AlertType.INICIO,
            )

            if already_sent:
                print(
                    f"   ⏭️ Start alert already sent to: "
                    f"{name} ({email})"
                )
                continue

            # Send email
            success = self.email_dispatcher.send_alert_start(
                to_email=email,
                responsible_name=name,
                activity_name=activity_name,
                start_date=start_date,
                end_date=end_date,
                project_name=project_name
            )
            
            if success:
                # Save history only after successful sending
                self.system_repository.save_alert_history(
                    AlertHistory(
                        project=project_name,
                        activity=activity_name,
                        researcher=name,
                        email=email,
                        alert_type=AlertType.INICIO,
                    )
                )

                self.stats["alerts_start"] += 1

                print(
                    f"   ✅ Start alert sent to: "
                    f"{name} ({email})"
                )

            else:
                error_msg = (
                    f"Failed to send start alert to "
                    f"{email} for {activity_name}"
                )

                self.stats["errors"].append(error_msg)

                print(f"   ❌ {error_msg}")


    def _send_3_days_alerts(
        self,
        recipients: List[Tuple[str, str]],
        activity_name: str,
        end_date: str,
        project_name: str,
        reference_date: date,
    ):
        """
        Send a reminder alert when an activity is 3 days away
        from its deadline.

        The alert is sent only once per
        project/activity/researcher.
        """

        for name, email in recipients:

            # Check whether this reminder was already sent
            already_sent = self.system_repository.alert_was_sent(
                project=project_name,
                activity=activity_name,
                researcher=name,
                alert_type=AlertType.FALTA_3_DIAS,
            )

            if already_sent:
                print(
                    f"   ⏭️ 3-day reminder already sent to: "
                    f"{name} ({email})"
                )
                continue

            # Send email
            success = self.email_dispatcher.send_alert_3_days(
                to_email=email,
                responsible_name=name,
                activity_name=activity_name,
                end_date=end_date,
                project_name=project_name,
            )

            # Save history only after successful sending
            if success:
                self.system_repository.save_alert_history(
                    AlertHistory(
                        project=project_name,
                        activity=activity_name,
                        researcher=name,
                        email=email,
                        alert_type=AlertType.FALTA_3_DIAS,
                        reference_date=reference_date,
                    )
                )

                self.stats["alerts_3_days"] += 1

                print(
                    f"   ⏰ 3-day reminder sent to: "
                    f"{name} ({email})"
                )

            else:
                error_msg = (
                    f"Failed to send 3-day reminder to "
                    f"{email} for {activity_name}"
                )

                self.stats["errors"].append(error_msg)

                print(f"   ❌ {error_msg}")


    def _send_1_day_alerts(
        self,
        recipients: List[Tuple[str, str]],
        activity_name: str,
        end_date: str,
        project_name: str,
        reference_date: date,
    ):
        """
        Send a reminder alert when an activity is 1 day away
        from its deadline.

        The alert is sent only once per
        project/activity/researcher.
        """

        for name, email in recipients:

            already_sent = self.system_repository.alert_was_sent(
                project=project_name,
                activity=activity_name,
                researcher=name,
                alert_type=AlertType.FALTA_1_DIA,
            )

            if already_sent:
                print(
                    f"   ⏭️ 1-day reminder already sent to: "
                    f"{name} ({email})"
                )
                continue

            success = self.email_dispatcher.send_alert_1_day(
                to_email=email,
                responsible_name=name,
                activity_name=activity_name,
                end_date=end_date,
                project_name=project_name,
            )

            if success:
                self.system_repository.save_alert_history(
                    AlertHistory(
                        project=project_name,
                        activity=activity_name,
                        researcher=name,
                        email=email,
                        alert_type=AlertType.FALTA_1_DIA,
                        reference_date=reference_date,
                    )
                )

                self.stats["alerts_1_day"] += 1

                print(
                    f"   ⚠️ 1-day reminder sent to: "
                    f"{name} ({email})"
                )

            else:
                error_msg = (
                    f"Failed to send 1-day reminder to "
                    f"{email} for {activity_name}"
                )

                self.stats["errors"].append(error_msg)

                print(f"   ❌ {error_msg}")

    
    def _send_delay_alerts(
            self, 
            recipients: List[Tuple[str, str]],
            activity_name: str, 
            end_date: str,
            days_delayed: int, 
            project_name: str,
            reference_date: date,
    ):
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
            already_sent = self.system_repository.alert_was_sent(
                project=project_name,
                activity=activity_name,
                researcher=name,
                alert_type=AlertType.ATRASO,
                reference_date=reference_date,
            )

            if already_sent:
                print(
                    f"   ⏭️ Delay alert already sent today to: "
                    f"{name} ({email})"
                )
                continue

            success = self.email_dispatcher.send_alert_delay(
                to_email=email,
                responsible_name=name,
                activity_name=activity_name,
                end_date=end_date,
                days_delayed=days_delayed,
                project_name=project_name,
            )

            if success:
                self.system_repository.save_alert_history(
                    AlertHistory(
                        project=project_name,
                        activity=activity_name,
                        researcher=name,
                        email=email,
                        alert_type=AlertType.ATRASO,
                        reference_date=reference_date,
                    )
                )

                self.stats["alerts_delay"] += 1

                print(
                    f"   ⚠️ Delay alert sent to: "
                    f"{name} ({email}) - {days_delayed} days"
                )
            else:
                error_msg = (
                    f"Failed to send delay alert to "
                    f"{email} for {activity_name}"
                )
                self.stats["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
    
    def _send_completion_alerts(
            self, 
            recipients: List[Tuple[str, str]],
            activity_name: str, 
            project_name: str,
    ):
        """
        Send completion alerts to all recipients.
        
        Args:
            recipients: List of (name, email) tuples
            activity_name: Name of the activity
            project_name: Name of the project
        """

        for name, email in recipients:
            already_sent = self.system_repository.alert_was_sent(
                project=project_name,
                activity=activity_name,
                researcher=name,
                alert_type=AlertType.CONCLUSAO,
        )

            if already_sent:
                print(
                    f"   ⏭️ Completion alert already sent to: "
                    f"{name} ({email})"
                )
                continue

            success = self.email_dispatcher.send_alert_completion(
                    to_email=email,
                    responsible_name=name,
                    activity_name=activity_name,
                    project_name=project_name,
            )
                
            if success:
                self.system_repository.save_alert_history(
                    AlertHistory(
                        project=project_name,
                        activity=activity_name,
                        researcher=name,
                        email=email,
                        alert_type=AlertType.CONCLUSAO,
                    )
                )

                self.stats["alerts_completion"] += 1

                print(
                    f"   ✅ Completion alert sent to: "
                    f"{name} ({email})"
                )
            else:
                error_msg = (
                    f"Failed to send completion alert to " 
                    f"{email} for {activity_name}"
                )
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
        print(f"   3-day reminders sent: {self.stats['alerts_3_days']}")
        print(f"   1-day reminders sent: {self.stats['alerts_1_day']}")
        print(f"   Errors: {len(self.stats['errors'])}")
        print("="*60)
    
    def process_single_project(self, project_name: str) -> Dict[str, Any]:
        """
        Process a single project by name.

        The project must be registered in the control spreadsheet.
        Only active projects are processed.
        
        Args:
            project_name: Name of the project in PROJECTS worksheet.
            
        Returns:
            Dictionary with execution statistics
        """        
        # Reset statistics
        self._reset_stats()
        
        print("\n" + "="*60)
        print(
            f"🚀 STARTING SINGLE PROJECT: "
            f"{project_name.upper()}"
        )
        print("="*60)

        # Get project state from control spreadsheet
        project_state = self.system_repository.get_project_state(
            project_name
        )

        # Project must exist in PROJECTS
        if project_state is None:
            error_msg = (
                f"Project '{project_name}' not found in control spreadsheet"
            )
            print(f"❌ {error_msg}")
            return {"error": error_msg}

        # Respect the active flag
        if not project_state.active:
            print(
                f"⏸️ Project inactive, skipping: "
                f"{project_name.upper()}"
            )

            return {
                "project": project_name,
                "total_activities": 0,
                "alerts_sent": {
                    "start": 0,
                    "delay": 0,
                    "completion": 0,
                    "3_days": 0,
                    "1_day": 0,
                },
                "errors": [],
            }

        spreadsheet_id = project_state.spreadsheet_id

        self._process_single_spreadsheet(
            spreadsheet_id,
            project_name,
        )

        self.stats["total_spreadsheets"] += 1

        self._print_summary()

        return {
            "project": project_name,
            "total_spreadsheets": self.stats["total_spreadsheets"],
            "total_activities": self.stats["total_activities"],
            "alerts_sent": {
                "start": self.stats["alerts_start"],
                "delay": self.stats["alerts_delay"],
                "completion": self.stats["alerts_completion"],
                "3_days": self.stats["alerts_3_days"],
                "1_day": self.stats["alerts_1_day"],
            },
            "errors": self.stats["errors"],
        }
