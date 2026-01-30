#!/usr/bin/env python3
"""
CLI Todo Application

A simple, single-file todo application with JSON-based persistence.
Supports add, list, complete, and delete operations with atomic file operations
and comprehensive error handling.

Usage:
    todo add "Task description"
    todo list [--all] [--completed]
    todo complete <task_id>
    todo delete <task_id>
    todo --help
"""

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import shutil
import fcntl
import time


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Task:
    """
    Represents a single todo task.
    
    Attributes:
        id: Unique identifier (UUID4)
        title: Task description (1-500 characters)
        completed: Completion status
        created_at: ISO 8601 timestamp of creation
        completed_at: ISO 8601 timestamp of completion (None if not completed)
    """
    id: str
    title: str
    completed: bool
    created_at: str
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary loaded from JSON."""
        return cls(**data)
    
    def validate(self) -> None:
        """
        Validate task data.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Task title cannot be empty")
        if len(self.title) > 500:
            raise ValueError("Task title cannot exceed 500 characters")


# ============================================================================
# STORAGE MANAGER
# ============================================================================

class StorageManager:
    """
    Manages atomic read/write operations to the JSON file.
    
    Implements file locking and backup mechanisms to prevent data corruption.
    """
    
    def __init__(self, file_path: Path):
        """
        Initialize storage manager.
        
        Args:
            file_path: Path to the JSON storage file
        """
        self.file_path = file_path
        self.backup_path = file_path.with_suffix('.json.backup')
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create initial empty file if it doesn't exist
        if not self.file_path.exists():
            self._write_tasks([])
    
    def load(self) -> List[Dict[str, Any]]:
        """
        Load tasks from JSON file with error recovery.
        
        Returns:
            List of task dictionaries
            
        Raises:
            SystemExit: On unrecoverable errors
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    content = f.read()
                    if not content.strip():
                        return []
                    data = json.loads(content)
                    
                    # Validate JSON structure
                    if not isinstance(data, list):
                        raise ValueError("Invalid JSON structure: expected list")
                    
                    return data
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    
        except FileNotFoundError:
            # File doesn't exist yet, return empty list
            return []
        except json.JSONDecodeError as e:
            # Attempt recovery from backup
            return self._recover_from_backup(e)
        except Exception as e:
            print(f"Error: Failed to load tasks: {e}", file=sys.stderr)
            sys.exit(2)
    
    def save(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Save tasks to JSON file atomically with backup.
        
        Args:
            tasks: List of task dictionaries to save
            
        Raises:
            SystemExit: On save failure
        """
        # Create backup before writing
        self._create_backup()
        
        # Use atomic write: write to temp file, then rename
        temp_path = self.file_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                # Acquire exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(tasks, f, indent=2, ensure_ascii=False)
                    f.flush()
                    # Ensure data is written to disk
                    import os
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # Atomic rename operation
            shutil.move(str(temp_path), str(self.file_path))
            
        except Exception as e:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            print(f"Error: Failed to save tasks: {e}", file=sys.stderr)
            print("Your changes were not saved. Please try again.", file=sys.stderr)
            sys.exit(2)
    
    def _write_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """Write tasks directly without backup (used for initialization)."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    def _create_backup(self) -> None:
        """Create backup of current tasks file."""
        if self.file_path.exists():
            try:
                shutil.copy2(str(self.file_path), str(self.backup_path))
            except Exception as e:
                # Backup failure shouldn't stop the operation, but warn user
                print(f"Warning: Failed to create backup: {e}", file=sys.stderr)
    
    def _recover_from_backup(self, original_error: Exception) -> List[Dict[str, Any]]:
        """
        Attempt to recover from backup file.
        
        Args:
            original_error: The error that triggered recovery
            
        Returns:
            List of recovered tasks
            
        Raises:
            SystemExit: If recovery fails
        """
        print(f"Error: JSON file corrupted: {original_error}", file=sys.stderr)
        
        if self.backup_path.exists():
            print("Attempting to recover from backup...", file=sys.stderr)
            try:
                with open(self.backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Restore from backup
                    shutil.copy2(str(self.backup_path), str(self.file_path))
                    print("Successfully recovered from backup!", file=sys.stderr)
                    return data
            except Exception as e:
                print(f"Error: Failed to recover from backup: {e}", file=sys.stderr)
        
        print("\nYour tasks file is corrupted and no backup is available.", file=sys.stderr)
        print("Starting with an empty task list.", file=sys.stderr)
        return []


# ============================================================================
# TASK MANAGER
# ============================================================================

class TaskManager:
    """
    Encapsulates all todo operations with validation and business logic.
    """
    
    def __init__(self, storage: StorageManager):
        """
        Initialize task manager.
        
        Args:
            storage: StorageManager instance for persistence
        """
        self.storage = storage
    
    def add_task(self, title: str) -> Task:
        """
        Add a new task.
        
        Args:
            title: Task description
            
        Returns:
            The created Task object
            
        Raises:
            ValueError: If title is invalid
        """
        # Validate and sanitize title
        title = title.strip()
        if not title:
            raise ValueError("Task title cannot be empty")
        if len(title) > 500:
            raise ValueError("Task title cannot exceed 500 characters")
        
        # Create new task
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            completed=False,
            created_at=datetime.now().isoformat(),
            completed_at=None
        )
        
        # Load existing tasks
        tasks_data = self.storage.load()
        tasks = [Task.from_dict(t) for t in tasks_data]
        
        # Add new task
        tasks.append(task)
        
        # Save back to storage
        self.storage.save([t.to_dict() for t in tasks])
        
        return task
    
    def list_tasks(self, filter_type: str = "pending") -> List[Task]:
        """
        List tasks with optional filtering.
        
        Args:
            filter_type: "all", "pending", or "completed"
            
        Returns:
            List of Task objects matching the filter
        """
        tasks_data = self.storage.load()
        tasks = [Task.from_dict(t) for t in tasks_data]
        
        if filter_type == "completed":
            return [t for t in tasks if t.completed]
        elif filter_type == "pending":
            return [t for t in tasks if not t.completed]
        else:  # "all"
            return tasks
    
    def complete_task(self, task_id: str) -> Task:
        """
        Mark a task as completed.
        
        Args:
            task_id: ID of the task to complete
            
        Returns:
            The completed Task object
            
        Raises:
            ValueError: If task not found or already completed
        """
        tasks_data = self.storage.load()
        tasks = [Task.from_dict(t) for t in tasks_data]
        
        # Find task by ID
        task = self._find_task_by_id(tasks, task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        if task.completed:
            raise ValueError("Task is already completed")
        
        # Mark as completed
        task.completed = True
        task.completed_at = datetime.now().isoformat()
        
        # Save updated tasks
        self.storage.save([t.to_dict() for t in tasks])
        
        return task
    
    def delete_task(self, task_id: str) -> Task:
        """
        Delete a task.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            The deleted Task object
            
        Raises:
            ValueError: If task not found
        """
        tasks_data = self.storage.load()
        tasks = [Task.from_dict(t) for t in tasks_data]
        
        # Find task by ID
        task = self._find_task_by_id(tasks, task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Remove task
        tasks = [t for t in tasks if t.id != task_id]
        
        # Save updated tasks
        self.storage.save([t.to_dict() for t in tasks])
        
        return task
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID to lookup
            
        Returns:
            Task object or None if not found
        """
        tasks_data = self.storage.load()
        tasks = [Task.from_dict(t) for t in tasks_data]
        return self._find_task_by_id(tasks, task_id)
    
    @staticmethod
    def _find_task_by_id(tasks: List[Task], task_id: str) -> Optional[Task]:
        """
        Find task in list by ID (case-insensitive prefix match).
        
        Args:
            tasks: List of tasks to search
            task_id: Task ID to find (can be a prefix)
            
        Returns:
            Task object or None if not found
        """
        task_id_lower = task_id.lower()
        
        # First try exact match
        for task in tasks:
            if task.id.lower() == task_id_lower:
                return task
        
        # Then try prefix match
        matches = [t for t in tasks if t.id.lower().startswith(task_id_lower)]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # Multiple matches - ambiguous
            raise ValueError(f"Ambiguous task ID '{task_id}'. Please provide more characters.")
        
        return None


# ============================================================================
# CLI INTERFACE
# ============================================================================

class TodoCLI:
    """Command-line interface for the todo application."""
    
    # ANSI color codes for output formatting
    COLORS = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'gray': '\033[90m',
        'reset': '\033[0m',
        'bold': '\033[1m',
    }
    
    def __init__(self, task_manager: TaskManager):
        """
        Initialize CLI interface.
        
        Args:
            task_manager: TaskManager instance
        """
        self.task_manager = task_manager
        self.use_colors = sys.stdout.isatty()  # Only use colors if output is a terminal
    
    def _colorize(self, text: str, color: str) -> str:
        """
        Apply color to text if colors are enabled.
        
        Args:
            text: Text to colorize
            color: Color name from COLORS dict
            
        Returns:
            Colored text or plain text if colors disabled
        """
        if not self.use_colors:
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def cmd_add(self, args: argparse.Namespace) -> int:
        """
        Handle 'add' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            task = self.task_manager.add_task(args.title)
            print(self._colorize("✓", "green") + f" Added task: {task.title}")
            print(f"  ID: {self._colorize(task.id[:8], 'gray')}")
            return 0
        except ValueError as e:
            print(self._colorize(f"Error: {e}", "red"), file=sys.stderr)
            return 1
    
    def cmd_list(self, args: argparse.Namespace) -> int:
        """
        Handle 'list' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success)
        """
        # Determine filter type
        if args.all:
            filter_type = "all"
        elif args.completed:
            filter_type = "completed"
        else:
            filter_type = "pending"
        
        tasks = self.task_manager.list_tasks(filter_type)
        
        if not tasks:
            if filter_type == "all":
                print(self._colorize("No tasks yet. Add one with 'todo add \"Task description\"'", "gray"))
            elif filter_type == "completed":
                print(self._colorize("No completed tasks.", "gray"))
            else:
                print(self._colorize("No pending tasks. Great job! 🎉", "gray"))
            return 0
        
        # Display header
        header = {
            "all": "All Tasks",
            "completed": "Completed Tasks",
            "pending": "Pending Tasks"
        }[filter_type]
        print(self._colorize(f"\n{header} ({len(tasks)}):", "bold"))
        print()
        
        # Display tasks
        for task in tasks:
            self._print_task(task)
        
        print()  # Empty line at the end
        return 0
    
    def _print_task(self, task: Task) -> None:
        """
        Print a single task with formatting.
        
        Args:
            task: Task to print
        """
        # Status indicator
        if task.completed:
            status = self._colorize("✓", "green")
            title_color = "gray"
        else:
            status = self._colorize("○", "yellow")
            title_color = "reset"
        
        # Task ID (shortened)
        task_id = self._colorize(task.id[:8], "gray")
        
        # Task title
        title = self._colorize(task.title, title_color)
        
        # Print task line
        print(f"{status} [{task_id}] {title}")
        
        # Additional info for completed tasks
        if task.completed and task.completed_at:
            completed_date = self._format_datetime(task.completed_at)
            print(f"  {self._colorize(f'Completed: {completed_date}', 'gray')}")
    
    def cmd_complete(self, args: argparse.Namespace) -> int:
        """
        Handle 'complete' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            task = self.task_manager.complete_task(args.task_id)
            print(self._colorize("✓", "green") + f" Completed: {task.title}")
            return 0
        except ValueError as e:
            print(self._colorize(f"Error: {e}", "red"), file=sys.stderr)
            return 1
    
    def cmd_delete(self, args: argparse.Namespace) -> int:
        """
        Handle 'delete' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            task = self.task_manager.delete_task(args.task_id)
            print(self._colorize("✓", "green") + f" Deleted: {task.title}")
            return 0
        except ValueError as e:
            print(self._colorize(f"Error: {e}", "red"), file=sys.stderr)
            return 1
    
    @staticmethod
    def _format_datetime(iso_datetime: str) -> str:
        """
        Format ISO datetime string for display.
        
        Args:
            iso_datetime: ISO 8601 datetime string
            
        Returns:
            Formatted datetime string
        """
        try:
            dt = datetime.fromisoformat(iso_datetime)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return iso_datetime


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='todo',
        description='A simple CLI todo application',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  todo add "Buy groceries"           Add a new task
  todo list                          List pending tasks
  todo list --all                    List all tasks
  todo list --completed              List completed tasks
  todo complete abc123               Complete a task (by ID prefix)
  todo delete abc123                 Delete a task (by ID prefix)

Storage:
  Tasks are stored in ~/.todo/tasks.json
  Automatic backups are created before each save
        """
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('title', help='Task description')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_group = list_parser.add_mutually_exclusive_group()
    list_group.add_argument('--all', action='store_true', help='Show all tasks')
    list_group.add_argument('--completed', action='store_true', help='Show only completed tasks')
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Mark a task as completed')
    complete_parser.add_argument('task_id', help='Task ID (or ID prefix)')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('task_id', help='Task ID (or ID prefix)')
    
    return parser


def main() -> int:
    """
    Main entry point for the CLI application.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Parse command-line arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 0
    
    # Initialize components
    storage_path = Path.home() / '.todo' / 'tasks.json'
    storage = StorageManager(storage_path)
    task_manager = TaskManager(storage)
    cli = TodoCLI(task_manager)
    
    # Route to appropriate command handler
    command_handlers = {
        'add': cli.cmd_add,
        'list': cli.cmd_list,
        'complete': cli.cmd_complete,
        'delete': cli.cmd_delete,
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        try:
            return handler(args)
        except KeyboardInterrupt:
            print("\nOperation cancelled.", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 2
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())