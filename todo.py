#!/usr/bin/env python3
"""
CLI Todo Application

A simple command-line todo list manager using Python standard library only.
Stores tasks in JSON format in the user's home directory (~/.todo.json).

Usage:
    todo add "Task description"
    todo list [--all | --pending | --completed]
    todo complete <task-id>
    todo delete <task-id>
"""

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
import shutil

# Application version
VERSION = "1.0.0"

# Data file location
DATA_FILE = Path.home() / ".todo.json"
BACKUP_FILE = Path.home() / ".todo.json.backup"


@dataclass
class Task:
    """
    Represents a single todo task.
    
    Attributes:
        id: Unique identifier (UUID4)
        description: Task description text
        completed: Whether the task is completed
        created_at: ISO timestamp of task creation
    """
    id: str
    description: str
    completed: bool
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary loaded from JSON."""
        return cls(
            id=data['id'],
            description=data['description'],
            completed=data['completed'],
            created_at=data['created_at']
        )
    
    def get_short_id(self, length: int = 8) -> str:
        """Get shortened version of UUID for display."""
        return self.id[:length]
    
    def format_created_at(self) -> str:
        """Format creation timestamp for display."""
        try:
            dt = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, AttributeError):
            return self.created_at


class DataStore:
    """
    Handles all data persistence operations with JSON file storage.
    
    Provides atomic writes, backup creation, and error recovery for the task list.
    """
    
    def __init__(self, file_path: Path = DATA_FILE):
        """
        Initialize data store with file path.
        
        Args:
            file_path: Path to the JSON data file
        """
        self.file_path = file_path
        self.backup_path = BACKUP_FILE
    
    def load_tasks(self) -> List[Task]:
        """
        Load all tasks from JSON file.
        
        Returns:
            List of Task objects
            
        Raises:
            DataStoreError: If file is corrupted or cannot be read
        """
        # Create file if it doesn't exist
        if not self.file_path.exists():
            self._initialize_file()
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate schema version
            if 'version' not in data:
                print("Warning: Legacy data format detected, migrating...", 
                      file=sys.stderr)
            
            # Extract tasks
            task_data = data.get('tasks', [])
            tasks = [Task.from_dict(t) for t in task_data]
            return tasks
            
        except json.JSONDecodeError as e:
            # Try to recover from backup
            if self.backup_path.exists():
                print(f"Error: Corrupted data file. Attempting recovery from backup...",
                      file=sys.stderr)
                try:
                    return self._recover_from_backup()
                except Exception as backup_error:
                    raise DataStoreError(
                        f"Failed to load tasks and backup recovery failed: {backup_error}"
                    ) from e
            else:
                raise DataStoreError(
                    f"Corrupted data file and no backup available: {e}"
                ) from e
                
        except (OSError, IOError) as e:
            raise DataStoreError(f"Cannot read data file: {e}") from e
        except (KeyError, TypeError) as e:
            raise DataStoreError(f"Invalid data format: {e}") from e
    
    def save_tasks(self, tasks: List[Task]) -> None:
        """
        Save tasks to JSON file with atomic write.
        
        Args:
            tasks: List of Task objects to save
            
        Raises:
            DataStoreError: If file cannot be written
        """
        # Create backup of existing file
        if self.file_path.exists():
            try:
                shutil.copy2(self.file_path, self.backup_path)
            except (OSError, IOError) as e:
                print(f"Warning: Could not create backup: {e}", file=sys.stderr)
        
        # Prepare data structure
        data = {
            'version': VERSION,
            'tasks': [task.to_dict() for task in tasks]
        }
        
        # Atomic write using temp file + rename
        temp_file = self.file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write('\n')  # Ensure newline at end of file
            
            # Atomic rename (POSIX systems guarantee atomicity)
            os.replace(temp_file, self.file_path)
            
            # Set file permissions to user-only read/write
            try:
                os.chmod(self.file_path, 0o600)
            except (OSError, AttributeError):
                # May fail on Windows, but not critical
                pass
                
        except (OSError, IOError) as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise DataStoreError(f"Cannot save tasks: {e}") from e
    
    def _initialize_file(self) -> None:
        """Create new data file with empty task list."""
        initial_data = {
            'version': VERSION,
            'tasks': []
        }
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2)
                f.write('\n')
            
            # Set restrictive permissions
            try:
                os.chmod(self.file_path, 0o600)
            except (OSError, AttributeError):
                pass
                
        except (OSError, IOError) as e:
            raise DataStoreError(f"Cannot create data file: {e}") from e
    
    def _recover_from_backup(self) -> List[Task]:
        """Attempt to recover data from backup file."""
        with open(self.backup_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
        
        # Restore backup to main file
        shutil.copy2(self.backup_path, self.file_path)
        print("✓ Successfully recovered from backup", file=sys.stderr)
        
        return tasks


class TaskManager:
    """
    Manages business logic for task operations.
    
    Handles CRUD operations, validation, and task filtering.
    """
    
    def __init__(self, data_store: DataStore):
        """
        Initialize task manager with data store.
        
        Args:
            data_store: DataStore instance for persistence
        """
        self.data_store = data_store
    
    def add_task(self, description: str) -> Task:
        """
        Create and add a new task.
        
        Args:
            description: Task description text
            
        Returns:
            The created Task object
            
        Raises:
            ValidationError: If description is empty
            DataStoreError: If save fails
        """
        if not description or not description.strip():
            raise ValidationError("Task description cannot be empty")
        
        # Create new task
        task = Task(
            id=str(uuid.uuid4()),
            description=description.strip(),
            completed=False,
            created_at=datetime.utcnow().isoformat() + 'Z'
        )
        
        # Load existing tasks, add new one, and save
        tasks = self.data_store.load_tasks()
        tasks.append(task)
        self.data_store.save_tasks(tasks)
        
        return task
    
    def get_all_tasks(self, filter_status: Optional[str] = None) -> List[Task]:
        """
        Retrieve all tasks, optionally filtered by status.
        
        Args:
            filter_status: 'pending', 'completed', or None for all
            
        Returns:
            List of Task objects
        """
        tasks = self.data_store.load_tasks()
        
        if filter_status == 'pending':
            return [t for t in tasks if not t.completed]
        elif filter_status == 'completed':
            return [t for t in tasks if t.completed]
        else:
            return tasks
    
    def complete_task(self, task_id: str) -> Task:
        """
        Mark a task as completed.
        
        Args:
            task_id: Full or partial task ID (minimum 4 characters)
            
        Returns:
            The completed Task object
            
        Raises:
            ValidationError: If task ID is invalid or not found
            DataStoreError: If save fails
        """
        tasks = self.data_store.load_tasks()
        task = self._find_task_by_id(tasks, task_id)
        
        if task.completed:
            raise ValidationError(f"Task is already completed: {task.description}")
        
        task.completed = True
        self.data_store.save_tasks(tasks)
        
        return task
    
    def delete_task(self, task_id: str) -> Task:
        """
        Delete a task.
        
        Args:
            task_id: Full or partial task ID (minimum 4 characters)
            
        Returns:
            The deleted Task object
            
        Raises:
            ValidationError: If task ID is invalid or not found
            DataStoreError: If save fails
        """
        tasks = self.data_store.load_tasks()
        task = self._find_task_by_id(tasks, task_id)
        
        # Remove task from list
        tasks = [t for t in tasks if t.id != task.id]
        self.data_store.save_tasks(tasks)
        
        return task
    
    def _find_task_by_id(self, tasks: List[Task], task_id: str) -> Task:
        """
        Find task by full or partial ID.
        
        Args:
            tasks: List of tasks to search
            task_id: Full or partial UUID (minimum 4 characters)
            
        Returns:
            Matching Task object
            
        Raises:
            ValidationError: If ID is too short, not found, or ambiguous
        """
        if len(task_id) < 4:
            raise ValidationError(
                "Task ID must be at least 4 characters long"
            )
        
        # Find matching tasks
        matches = [t for t in tasks if t.id.startswith(task_id)]
        
        if len(matches) == 0:
            raise ValidationError(
                f"Task not found: {task_id}"
            )
        elif len(matches) > 1:
            raise ValidationError(
                f"Ambiguous task ID '{task_id}' matches multiple tasks. "
                f"Please provide more characters."
            )
        
        return matches[0]


class TodoCLI:
    """
    Command-line interface for the todo application.
    
    Handles argument parsing and command routing.
    """
    
    def __init__(self, task_manager: TaskManager):
        """
        Initialize CLI with task manager.
        
        Args:
            task_manager: TaskManager instance for business logic
        """
        self.task_manager = task_manager
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser."""
        parser = argparse.ArgumentParser(
            prog='todo',
            description='Simple CLI todo list manager',
            epilog='Store your tasks and stay organized!'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version=f'%(prog)s {VERSION}'
        )
        
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            required=True
        )
        
        # Add command
        add_parser = subparsers.add_parser(
            'add',
            help='Add a new task'
        )
        add_parser.add_argument(
            'description',
            help='Task description'
        )
        
        # List command
        list_parser = subparsers.add_parser(
            'list',
            help='List tasks'
        )
        filter_group = list_parser.add_mutually_exclusive_group()
        filter_group.add_argument(
            '--all',
            action='store_const',
            const=None,
            dest='filter',
            help='Show all tasks (default)'
        )
        filter_group.add_argument(
            '--pending',
            action='store_const',
            const='pending',
            dest='filter',
            help='Show only pending tasks'
        )
        filter_group.add_argument(
            '--completed',
            action='store_const',
            const='completed',
            dest='filter',
            help='Show only completed tasks'
        )
        
        # Complete command
        complete_parser = subparsers.add_parser(
            'complete',
            help='Mark a task as completed'
        )
        complete_parser.add_argument(
            'task_id',
            help='Task ID (full or partial, min 4 chars)'
        )
        
        # Delete command
        delete_parser = subparsers.add_parser(
            'delete',
            help='Delete a task'
        )
        delete_parser.add_argument(
            'task_id',
            help='Task ID (full or partial, min 4 chars)'
        )
        
        return parser
    
    def run(self, args: List[str]) -> int:
        """
        Execute CLI command.
        
        Args:
            args: Command-line arguments (excluding program name)
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            parsed_args = self.parser.parse_args(args)
            
            if parsed_args.command == 'add':
                return self._cmd_add(parsed_args.description)
            elif parsed_args.command == 'list':
                return self._cmd_list(parsed_args.filter)
            elif parsed_args.command == 'complete':
                return self._cmd_complete(parsed_args.task_id)
            elif parsed_args.command == 'delete':
                return self._cmd_delete(parsed_args.task_id)
            else:
                print(f"Error: Unknown command: {parsed_args.command}", 
                      file=sys.stderr)
                return 1
                
        except (ValidationError, DataStoreError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\nOperation cancelled", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1
    
    def _cmd_add(self, description: str) -> int:
        """Handle 'add' command."""
        task = self.task_manager.add_task(description)
        print(f"✓ Task added: {task.description} (ID: {task.get_short_id()})")
        return 0
    
    def _cmd_list(self, filter_status: Optional[str]) -> int:
        """Handle 'list' command."""
        tasks = self.task_manager.get_all_tasks(filter_status)
        
        if not tasks:
            filter_msg = {
                'pending': 'No pending tasks',
                'completed': 'No completed tasks',
                None: 'No tasks found'
            }
            print(filter_msg.get(filter_status, 'No tasks found'))
            return 0
        
        # Group tasks by status
        pending = [t for t in tasks if not t.completed]
        completed = [t for t in tasks if t.completed]
        
        # Display pending tasks
        if pending and (filter_status is None or filter_status == 'pending'):
            print("\n[Pending]")
            for i, task in enumerate(pending, 1):
                print(f"  {i}. {task.get_short_id()} - {task.description} "
                      f"(Created: {task.format_created_at()})")
        
        # Display completed tasks
        if completed and (filter_status is None or filter_status == 'completed'):
            print("\n[Completed]")
            for i, task in enumerate(completed, 1):
                print(f"  {i}. {task.get_short_id()} - ✓ {task.description} "
                      f"(Created: {task.format_created_at()})")
        
        print()  # Empty line at end
        return 0
    
    def _cmd_complete(self, task_id: str) -> int:
        """Handle 'complete' command."""
        task = self.task_manager.complete_task(task_id)
        print(f"✓ Task completed: {task.description}")
        return 0
    
    def _cmd_delete(self, task_id: str) -> int:
        """Handle 'delete' command."""
        task = self.task_manager.delete_task(task_id)
        print(f"✓ Task deleted: {task.description}")
        return 0


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class DataStoreError(Exception):
    """Raised when data persistence operations fail."""
    pass


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Initialize components
        data_store = DataStore()
        task_manager = TaskManager(data_store)
        cli = TodoCLI(task_manager)
        
        # Run CLI with command-line arguments
        return cli.run(sys.argv[1:])
        
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())