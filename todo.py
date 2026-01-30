#!/usr/bin/env python3
"""
CLI Todo Application

A simple command-line todo list manager that stores todos in a JSON file.
All todos are persisted in ~/.todo.json for cross-session availability.

Usage:
    python todo.py add "Buy groceries"
    python todo.py list
    python todo.py complete 1
    python todo.py delete 1
    python todo.py --help

Requirements:
    - Python 3.7 or higher (for dataclass support)
    - No external dependencies (stdlib only)
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants
VERSION = "1.0.0"
STORAGE_FILENAME = ".todo.json"


@dataclass
class Todo:
    """
    Represents a single todo item.
    
    Attributes:
        id: Unique identifier for the todo
        description: Text description of the task
        completed: Whether the task is completed
        created_at: ISO timestamp of when the todo was created
    """
    id: int
    description: str
    completed: bool
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert Todo to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Todo':
        """Create Todo instance from dictionary."""
        return cls(**data)


class TodoStorage:
    """
    Handles persistence of todos to JSON file on disk.
    
    Provides atomic write operations and manages the storage file location
    in the user's home directory (~/.todo.json).
    """

    def __init__(self):
        self.storage_path = self.get_storage_path()
        self.initialize_storage()

    @staticmethod
    def get_storage_path() -> Path:
        """
        Get the path to the storage file.
        
        Returns:
            Path object pointing to ~/.todo.json
        """
        return Path.home() / STORAGE_FILENAME

    def initialize_storage(self) -> None:
        """
        Create storage file with empty structure if it doesn't exist.
        """
        if not self.storage_path.exists():
            self.save({"todos": [], "next_id": 1})

    def load(self) -> Dict[str, Any]:
        """
        Load todos from storage file.
        
        Returns:
            Dictionary with 'todos' list and 'next_id' counter
            
        Raises:
            SystemExit: If file is corrupted or cannot be read
        """
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate structure
            if not isinstance(data, dict) or 'todos' not in data or 'next_id' not in data:
                raise ValueError("Invalid storage file structure")
                
            return data
            
        except json.JSONDecodeError as e:
            print(f"Error: Storage file is corrupted at {self.storage_path}", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
            print("Please fix or delete the file to continue.", file=sys.stderr)
            sys.exit(1)
        except (IOError, PermissionError) as e:
            print(f"Error: Cannot read storage file at {self.storage_path}", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            print(f"Storage file location: {self.storage_path}", file=sys.stderr)
            sys.exit(1)

    def save(self, data: Dict[str, Any]) -> None:
        """
        Save todos to storage file using atomic write pattern.
        
        Writes to a temporary file first, then renames to ensure
        atomicity and prevent corruption.
        
        Args:
            data: Dictionary containing 'todos' and 'next_id'
            
        Raises:
            SystemExit: If file cannot be written
        """
        temp_path = self.storage_path.with_suffix('.tmp')
        
        try:
            # Write to temporary file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.replace(self.storage_path)
            
        except (IOError, PermissionError) as e:
            print(f"Error: Cannot write to storage file at {self.storage_path}", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
            if temp_path.exists():
                temp_path.unlink()
            sys.exit(1)


class TodoManager:
    """
    Manages business logic for todo operations.
    
    Handles CRUD operations and enforces business rules like
    unique IDs and data validation.
    """

    def __init__(self):
        self.storage = TodoStorage()

    def add_todo(self, description: str) -> Todo:
        """
        Create a new todo.
        
        Args:
            description: Text description of the task
            
        Returns:
            The created Todo object
            
        Raises:
            ValueError: If description is empty or invalid
        """
        # Validate description
        description = description.strip()
        if not description:
            raise ValueError("Todo description cannot be empty")
        
        if len(description) > 1000:
            raise ValueError("Todo description is too long (max 1000 characters)")
        
        # Load current state
        data = self.storage.load()
        
        # Create new todo
        todo = Todo(
            id=data['next_id'],
            description=description,
            completed=False,
            created_at=datetime.now().isoformat()
        )
        
        # Update state
        data['todos'].append(todo.to_dict())
        data['next_id'] += 1
        
        # Save
        self.storage.save(data)
        
        return todo

    def list_todos(self) -> List[Todo]:
        """
        Get all todos.
        
        Returns:
            List of Todo objects ordered by ID
        """
        data = self.storage.load()
        return [Todo.from_dict(todo_dict) for todo_dict in data['todos']]

    def complete_todo(self, todo_id: int) -> bool:
        """
        Mark a todo as completed.
        
        Args:
            todo_id: ID of the todo to complete
            
        Returns:
            True if todo was found and completed, False otherwise
        """
        data = self.storage.load()
        
        # Find todo by ID
        for todo_dict in data['todos']:
            if todo_dict['id'] == todo_id:
                todo_dict['completed'] = True
                self.storage.save(data)
                return True
        
        return False

    def delete_todo(self, todo_id: int) -> bool:
        """
        Delete a todo.
        
        Args:
            todo_id: ID of the todo to delete
            
        Returns:
            True if todo was found and deleted, False otherwise
        """
        data = self.storage.load()
        
        # Find and remove todo
        original_length = len(data['todos'])
        data['todos'] = [t for t in data['todos'] if t['id'] != todo_id]
        
        if len(data['todos']) < original_length:
            self.storage.save(data)
            return True
        
        return False


class TodoCLI:
    """
    Command-line interface for the todo application.
    
    Handles argument parsing, command routing, and output formatting.
    """

    def __init__(self):
        self.manager = TodoManager()
        self.parser = self.create_parser()

    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create and configure the argument parser.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            prog='todo',
            description='A simple CLI todo list manager',
            epilog='Todos are stored in ~/.todo.json'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version=f'%(prog)s {VERSION}'
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Add command
        add_parser = subparsers.add_parser(
            'add',
            help='Add a new todo'
        )
        add_parser.add_argument(
            'description',
            type=str,
            help='Description of the todo'
        )
        
        # List command
        subparsers.add_parser(
            'list',
            help='List all todos'
        )
        
        # Complete command
        complete_parser = subparsers.add_parser(
            'complete',
            help='Mark a todo as completed'
        )
        complete_parser.add_argument(
            'id',
            type=int,
            help='ID of the todo to complete'
        )
        
        # Delete command
        delete_parser = subparsers.add_parser(
            'delete',
            help='Delete a todo'
        )
        delete_parser.add_argument(
            'id',
            type=int,
            help='ID of the todo to delete'
        )
        
        return parser

    def display_todos(self, todos: List[Todo]) -> None:
        """
        Display todos in a formatted list.
        
        Args:
            todos: List of Todo objects to display
        """
        if not todos:
            print("No todos yet. Add one with: todo.py add \"Your task\"")
            return
        
        for todo in todos:
            checkbox = "[✓]" if todo.completed else "[ ]"
            print(f"{checkbox} {todo.id}. {todo.description}")

    def display_message(self, message: str, is_error: bool = False) -> None:
        """
        Display a message to the user.
        
        Args:
            message: Message text to display
            is_error: Whether this is an error message
        """
        if is_error:
            print(f"✗ {message}", file=sys.stderr)
        else:
            print(f"✓ {message}")

    def handle_add(self, args: argparse.Namespace) -> int:
        """
        Handle the 'add' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            todo = self.manager.add_todo(args.description)
            self.display_message(f"Added todo #{todo.id}: {todo.description}")
            return 0
        except ValueError as e:
            self.display_message(str(e), is_error=True)
            return 1

    def handle_list(self, args: argparse.Namespace) -> int:
        """
        Handle the 'list' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (always 0)
        """
        todos = self.manager.list_todos()
        self.display_todos(todos)
        return 0

    def handle_complete(self, args: argparse.Namespace) -> int:
        """
        Handle the 'complete' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        if args.id < 0:
            self.display_message("Error: Todo ID must be non-negative", is_error=True)
            return 1
        
        success = self.manager.complete_todo(args.id)
        if success:
            self.display_message(f"Completed todo #{args.id}")
            return 0
        else:
            self.display_message(f"Todo #{args.id} not found", is_error=True)
            return 1

    def handle_delete(self, args: argparse.Namespace) -> int:
        """
        Handle the 'delete' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        if args.id < 0:
            self.display_message("Error: Todo ID must be non-negative", is_error=True)
            return 1
        
        success = self.manager.delete_todo(args.id)
        if success:
            self.display_message(f"Deleted todo #{args.id}")
            return 0
        else:
            self.display_message(f"Todo #{args.id} not found", is_error=True)
            return 1

    def execute(self) -> int:
        """
        Parse arguments and execute the appropriate command.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        args = self.parser.parse_args()
        
        if args.command is None:
            self.parser.print_help()
            return 1
        
        # Route to appropriate handler
        handlers = {
            'add': self.handle_add,
            'list': self.handle_list,
            'complete': self.handle_complete,
            'delete': self.handle_delete
        }
        
        handler = handlers.get(args.command)
        if handler:
            return handler(args)
        else:
            self.parser.print_help()
            return 1


def check_python_version() -> None:
    """
    Check if Python version meets minimum requirements.
    
    Exits with error message if version is too old.
    """
    if sys.version_info < (3, 7):
        print("Error: This application requires Python 3.7 or higher", file=sys.stderr)
        print(f"Current version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Check Python version
    check_python_version()
    
    try:
        cli = TodoCLI()
        return cli.execute()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())