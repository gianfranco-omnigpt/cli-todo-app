#!/usr/bin/env python3
"""
CLI Todo App - A simple command-line task management tool.

This application provides basic task management functionality including:
- Adding new tasks
- Listing all tasks
- Completing tasks
- Deleting tasks

Tasks are persisted in a local JSON file (tasks.json) for data persistence.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional


# Constants
TASKS_FILE = "tasks.json"


def get_tasks_file_path() -> str:
    """
    Get the absolute path to the tasks.json file.
    
    The file is stored in the same directory as this script.
    
    Returns:
        str: Absolute path to tasks.json
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, TASKS_FILE)


def load_tasks() -> List[Dict]:
    """
    Load tasks from the JSON file.
    
    If the file doesn't exist, creates it with an empty array.
    If the file is corrupted, reinitializes it with an empty array.
    
    Returns:
        List[Dict]: List of task dictionaries
    """
    file_path = get_tasks_file_path()
    
    # Create file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []
    
    # Try to load existing file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
            if not isinstance(tasks, list):
                raise ValueError("Tasks file must contain a JSON array")
            return tasks
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Corrupted tasks file detected ({e}). Reinitializing...", 
              file=sys.stderr)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []


def save_tasks(tasks: List[Dict]) -> None:
    """
    Save tasks to the JSON file.
    
    Args:
        tasks: List of task dictionaries to save
    """
    file_path = get_tasks_file_path()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def get_next_id(tasks: List[Dict]) -> int:
    """
    Calculate the next available task ID.
    
    Args:
        tasks: List of existing tasks
        
    Returns:
        int: Next available ID (max existing ID + 1, or 1 if no tasks exist)
    """
    if not tasks:
        return 1
    return max(task['id'] for task in tasks) + 1


def add_task(task_text: str, tasks: List[Dict]) -> Dict:
    """
    Create a new task and add it to the task list.
    
    Args:
        task_text: Description of the task
        tasks: Existing list of tasks
        
    Returns:
        Dict: The newly created task
    """
    new_task = {
        'id': get_next_id(tasks),
        'text': task_text,
        'completed': False,
        'created_at': datetime.now().isoformat()
    }
    tasks.append(new_task)
    return new_task


def find_task_by_id(task_id: int, tasks: List[Dict]) -> Optional[Dict]:
    """
    Find a task by its ID.
    
    Args:
        task_id: ID of the task to find
        tasks: List of tasks to search
        
    Returns:
        Optional[Dict]: The task if found, None otherwise
    """
    for task in tasks:
        if task['id'] == task_id:
            return task
    return None


def complete_task(task_id: int, tasks: List[Dict]) -> bool:
    """
    Mark a task as completed.
    
    Args:
        task_id: ID of the task to complete
        tasks: List of tasks
        
    Returns:
        bool: True if task was found and completed, False otherwise
    """
    task = find_task_by_id(task_id, tasks)
    if task is None:
        return False
    task['completed'] = True
    return True


def delete_task(task_id: int, tasks: List[Dict]) -> bool:
    """
    Delete a task from the list.
    
    Args:
        task_id: ID of the task to delete
        tasks: List of tasks
        
    Returns:
        bool: True if task was found and deleted, False otherwise
    """
    task = find_task_by_id(task_id, tasks)
    if task is None:
        return False
    tasks.remove(task)
    return True


def format_task(task: Dict) -> str:
    """
    Format a task for display.
    
    Args:
        task: Task dictionary to format
        
    Returns:
        str: Formatted task string
    """
    status = "✓" if task['completed'] else " "
    task_id = task['id']
    text = task['text']
    
    # Format timestamp (just date and time, no seconds)
    try:
        created_dt = datetime.fromisoformat(task['created_at'])
        timestamp = created_dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, KeyError):
        timestamp = "Unknown"
    
    return f"[{task_id}] [{status}] {text} ({timestamp})"


def list_tasks(tasks: List[Dict]) -> None:
    """
    Display all tasks to stdout.
    
    Args:
        tasks: List of tasks to display
    """
    if not tasks:
        print("No tasks found.")
        return
    
    for task in tasks:
        print(format_task(task))


def handle_add(args: argparse.Namespace) -> None:
    """
    Handle the 'add' command.
    
    Args:
        args: Parsed command-line arguments
    """
    tasks = load_tasks()
    new_task = add_task(args.text, tasks)
    save_tasks(tasks)
    print(f"Added task #{new_task['id']}: {new_task['text']}")


def handle_list(args: argparse.Namespace) -> None:
    """
    Handle the 'list' command.
    
    Args:
        args: Parsed command-line arguments
    """
    tasks = load_tasks()
    list_tasks(tasks)


def handle_complete(args: argparse.Namespace) -> None:
    """
    Handle the 'complete' command.
    
    Args:
        args: Parsed command-line arguments
    """
    tasks = load_tasks()
    if complete_task(args.id, tasks):
        save_tasks(tasks)
        print(f"Marked task #{args.id} as complete")
    else:
        print(f"Error: Task #{args.id} not found", file=sys.stderr)
        sys.exit(1)


def handle_delete(args: argparse.Namespace) -> None:
    """
    Handle the 'delete' command.
    
    Args:
        args: Parsed command-line arguments
    """
    tasks = load_tasks()
    if delete_task(args.id, tasks):
        save_tasks(tasks)
        print(f"Deleted task #{args.id}")
    else:
        print(f"Error: Task #{args.id} not found", file=sys.stderr)
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured parser with all subcommands
    """
    parser = argparse.ArgumentParser(
        description="CLI Todo App - Manage your tasks from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add "Buy milk"           Add a new task
  %(prog)s list                     List all tasks
  %(prog)s complete 1               Mark task #1 as complete
  %(prog)s delete 1                 Delete task #1
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True
    
    # Add command
    parser_add = subparsers.add_parser('add', help='Add a new task')
    parser_add.add_argument('text', type=str, help='Task description')
    parser_add.set_defaults(func=handle_add)
    
    # List command
    parser_list = subparsers.add_parser('list', help='List all tasks')
    parser_list.set_defaults(func=handle_list)
    
    # Complete command
    parser_complete = subparsers.add_parser('complete', help='Mark a task as complete')
    parser_complete.add_argument('id', type=int, help='Task ID to complete')
    parser_complete.set_defaults(func=handle_complete)
    
    # Delete command
    parser_delete = subparsers.add_parser('delete', help='Delete a task')
    parser_delete.add_argument('id', type=int, help='Task ID to delete')
    parser_delete.set_defaults(func=handle_delete)
    
    return parser


def main() -> None:
    """
    Main entry point for the CLI application.
    """
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()