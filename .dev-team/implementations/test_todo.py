#!/usr/bin/env python3
"""
Unit tests for CLI Todo Application

Comprehensive test suite covering all commands, edge cases, and error scenarios.
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Add parent directory to path to import the todo module
sys.path.insert(0, os.path.dirname(__file__))
from software_engineer_unnamed_product import (
    Task, StorageManager, TaskManager, TodoCLI
)


class TestTask(unittest.TestCase):
    """Test cases for Task data model."""
    
    def test_task_creation(self):
        """Test creating a task with valid data."""
        task = Task(
            id="test-123",
            title="Test task",
            completed=False,
            created_at="2025-01-23T10:00:00"
        )
        self.assertEqual(task.id, "test-123")
        self.assertEqual(task.title, "Test task")
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)
    
    def test_task_to_dict(self):
        """Test serialization to dictionary."""
        task = Task(
            id="test-123",
            title="Test task",
            completed=False,
            created_at="2025-01-23T10:00:00"
        )
        task_dict = task.to_dict()
        self.assertIsInstance(task_dict, dict)
        self.assertEqual(task_dict['id'], "test-123")
        self.assertEqual(task_dict['title'], "Test task")
    
    def test_task_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'id': "test-123",
            'title': "Test task",
            'completed': False,
            'created_at': "2025-01-23T10:00:00",
            'completed_at': None
        }
        task = Task.from_dict(data)
        self.assertEqual(task.id, "test-123")
        self.assertEqual(task.title, "Test task")
    
    def test_task_validation_empty_title(self):
        """Test validation fails on empty title."""
        task = Task(
            id="test-123",
            title="",
            completed=False,
            created_at="2025-01-23T10:00:00"
        )
        with self.assertRaises(ValueError) as context:
            task.validate()
        self.assertIn("empty", str(context.exception).lower())
    
    def test_task_validation_long_title(self):
        """Test validation fails on title exceeding 500 characters."""
        task = Task(
            id="test-123",
            title="a" * 501,
            completed=False,
            created_at="2025-01-23T10:00:00"
        )
        with self.assertRaises(ValueError) as context:
            task.validate()
        self.assertIn("500", str(context.exception))


class TestStorageManager(unittest.TestCase):
    """Test cases for StorageManager."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / 'test_tasks.json'
        self.storage = StorageManager(self.storage_path)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_storage_initialization(self):
        """Test storage directory and file creation."""
        self.assertTrue(self.storage_path.exists())
        self.assertTrue(self.storage_path.parent.exists())
    
    def test_load_empty_storage(self):
        """Test loading from empty storage."""
        tasks = self.storage.load()
        self.assertEqual(tasks, [])
    
    def test_save_and_load(self):
        """Test saving and loading tasks."""
        test_tasks = [
            {
                'id': 'test-1',
                'title': 'Task 1',
                'completed': False,
                'created_at': '2025-01-23T10:00:00',
                'completed_at': None
            }
        ]
        self.storage.save(test_tasks)
        loaded_tasks = self.storage.load()
        self.assertEqual(len(loaded_tasks), 1)
        self.assertEqual(loaded_tasks[0]['title'], 'Task 1')
    
    def test_atomic_write_creates_backup(self):
        """Test that backup is created before writing."""
        # Save initial data
        initial_tasks = [
            {'id': 'test-1', 'title': 'Task 1', 'completed': False, 
             'created_at': '2025-01-23T10:00:00', 'completed_at': None}
        ]
        self.storage.save(initial_tasks)
        
        # Save new data (should create backup)
        new_tasks = [
            {'id': 'test-2', 'title': 'Task 2', 'completed': False,
             'created_at': '2025-01-23T11:00:00', 'completed_at': None}
        ]
        self.storage.save(new_tasks)
        
        # Check backup exists
        self.assertTrue(self.storage.backup_path.exists())
        
        # Verify backup contains initial data
        with open(self.storage.backup_path, 'r') as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data[0]['title'], 'Task 1')
    
    def test_load_corrupted_json_without_backup(self):
        """Test handling of corrupted JSON with no backup."""
        # Write corrupted JSON
        with open(self.storage_path, 'w') as f:
            f.write("{ invalid json }")
        
        # Should return empty list and not crash
        tasks = self.storage.load()
        self.assertEqual(tasks, [])


class TestTaskManager(unittest.TestCase):
    """Test cases for TaskManager."""
    
    def setUp(self):
        """Create temporary storage for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / 'test_tasks.json'
        self.storage = StorageManager(self.storage_path)
        self.manager = TaskManager(self.storage)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_task(self):
        """Test adding a new task."""
        task = self.manager.add_task("Test task")
        self.assertIsNotNone(task.id)
        self.assertEqual(task.title, "Test task")
        self.assertFalse(task.completed)
        self.assertIsNotNone(task.created_at)
    
    def test_add_task_strips_whitespace(self):
        """Test that task title whitespace is stripped."""
        task = self.manager.add_task("  Test task  ")
        self.assertEqual(task.title, "Test task")
    
    def test_add_task_empty_title(self):
        """Test adding task with empty title raises error."""
        with self.assertRaises(ValueError) as context:
            self.manager.add_task("")
        self.assertIn("empty", str(context.exception).lower())
    
    def test_add_task_title_too_long(self):
        """Test adding task with title exceeding 500 chars raises error."""
        with self.assertRaises(ValueError) as context:
            self.manager.add_task("a" * 501)
        self.assertIn("500", str(context.exception))
    
    def test_list_tasks_empty(self):
        """Test listing tasks when none exist."""
        tasks = self.manager.list_tasks()
        self.assertEqual(tasks, [])
    
    def test_list_tasks_all(self):
        """Test listing all tasks."""
        self.manager.add_task("Task 1")
        self.manager.add_task("Task 2")
        tasks = self.manager.list_tasks("all")
        self.assertEqual(len(tasks), 2)
    
    def test_list_tasks_pending(self):
        """Test listing only pending tasks."""
        task1 = self.manager.add_task("Task 1")
        task2 = self.manager.add_task("Task 2")
        self.manager.complete_task(task1.id)
        
        pending_tasks = self.manager.list_tasks("pending")
        self.assertEqual(len(pending_tasks), 1)
        self.assertEqual(pending_tasks[0].title, "Task 2")
    
    def test_list_tasks_completed(self):
        """Test listing only completed tasks."""
        task1 = self.manager.add_task("Task 1")
        task2 = self.manager.add_task("Task 2")
        self.manager.complete_task(task1.id)
        
        completed_tasks = self.manager.list_tasks("completed")
        self.assertEqual(len(completed_tasks), 1)
        self.assertEqual(completed_tasks[0].title, "Task 1")
    
    def test_complete_task(self):
        """Test completing a task."""
        task = self.manager.add_task("Test task")
        completed = self.manager.complete_task(task.id)
        
        self.assertTrue(completed.completed)
        self.assertIsNotNone(completed.completed_at)
    
    def test_complete_task_not_found(self):
        """Test completing non-existent task raises error."""
        with self.assertRaises(ValueError) as context:
            self.manager.complete_task("nonexistent-id")
        self.assertIn("not found", str(context.exception).lower())
    
    def test_complete_task_already_completed(self):
        """Test completing already completed task raises error."""
        task = self.manager.add_task("Test task")
        self.manager.complete_task(task.id)
        
        with self.assertRaises(ValueError) as context:
            self.manager.complete_task(task.id)
        self.assertIn("already completed", str(context.exception).lower())
    
    def test_complete_task_by_prefix(self):
        """Test completing task using ID prefix."""
        task = self.manager.add_task("Test task")
        prefix = task.id[:8]
        
        completed = self.manager.complete_task(prefix)
        self.assertTrue(completed.completed)
    
    def test_delete_task(self):
        """Test deleting a task."""
        task = self.manager.add_task("Test task")
        deleted = self.manager.delete_task(task.id)
        
        self.assertEqual(deleted.title, "Test task")
        tasks = self.manager.list_tasks()
        self.assertEqual(len(tasks), 0)
    
    def test_delete_task_not_found(self):
        """Test deleting non-existent task raises error."""
        with self.assertRaises(ValueError) as context:
            self.manager.delete_task("nonexistent-id")
        self.assertIn("not found", str(context.exception).lower())
    
    def test_get_task_by_id(self):
        """Test retrieving task by ID."""
        task = self.manager.add_task("Test task")
        retrieved = self.manager.get_task_by_id(task.id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test task")
    
    def test_get_task_by_id_not_found(self):
        """Test retrieving non-existent task returns None."""
        result = self.manager.get_task_by_id("nonexistent-id")
        self.assertIsNone(result)
    
    def test_ambiguous_task_id_prefix(self):
        """Test that ambiguous ID prefix raises appropriate error."""
        # Create tasks with IDs that have common prefix
        tasks_data = [
            {'id': 'abc12345', 'title': 'Task 1', 'completed': False,
             'created_at': '2025-01-23T10:00:00', 'completed_at': None},
            {'id': 'abc12678', 'title': 'Task 2', 'completed': False,
             'created_at': '2025-01-23T10:00:00', 'completed_at': None}
        ]
        self.storage.save(tasks_data)
        
        with self.assertRaises(ValueError) as context:
            self.manager.complete_task("abc12")
        self.assertIn("ambiguous", str(context.exception).lower())


class TestTodoCLI(unittest.TestCase):
    """Test cases for CLI interface."""
    
    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / 'test_tasks.json'
        self.storage = StorageManager(self.storage_path)
        self.manager = TaskManager(self.storage)
        self.cli = TodoCLI(self.manager)
        # Disable colors for consistent test output
        self.cli.use_colors = False
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_colorize_with_colors_disabled(self):
        """Test that colorize returns plain text when colors disabled."""
        result = self.cli._colorize("test", "green")
        self.assertEqual(result, "test")
    
    def test_format_datetime(self):
        """Test datetime formatting."""
        iso_datetime = "2025-01-23T10:30:45"
        formatted = self.cli._format_datetime(iso_datetime)
        self.assertIn("2025-01-23", formatted)
        self.assertIn("10:30", formatted)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / 'test_tasks.json'
        self.storage = StorageManager(self.storage_path)
        self.manager = TaskManager(self.storage)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """Test complete add-list-complete-delete workflow."""
        # Add tasks
        task1 = self.manager.add_task("Buy groceries")
        task2 = self.manager.add_task("Write documentation")
        task3 = self.manager.add_task("Review code")
        
        # List all tasks
        all_tasks = self.manager.list_tasks("all")
        self.assertEqual(len(all_tasks), 3)
        
        # Complete one task
        self.manager.complete_task(task1.id)
        
        # List pending tasks
        pending = self.manager.list_tasks("pending")
        self.assertEqual(len(pending), 2)
        
        # List completed tasks
        completed = self.manager.list_tasks("completed")
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].title, "Buy groceries")
        
        # Delete a task
        self.manager.delete_task(task2.id)
        
        # Verify final state
        all_tasks = self.manager.list_tasks("all")
        self.assertEqual(len(all_tasks), 2)
    
    def test_persistence_across_instances(self):
        """Test that tasks persist across StorageManager instances."""
        # Add task with first instance
        task = self.manager.add_task("Persistent task")
        
        # Create new instance with same storage path
        new_storage = StorageManager(self.storage_path)
        new_manager = TaskManager(new_storage)
        
        # Verify task exists
        tasks = new_manager.list_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Persistent task")
    
    def test_unicode_task_titles(self):
        """Test handling of Unicode characters in task titles."""
        unicode_titles = [
            "测试任务",  # Chinese
            "тестовая задача",  # Russian
            "タスク",  # Japanese
            "🎉 Celebration task"  # Emoji
        ]
        
        for title in unicode_titles:
            task = self.manager.add_task(title)
            self.assertEqual(task.title, title)
        
        # Verify all tasks loaded correctly
        tasks = self.manager.list_tasks()
        self.assertEqual(len(tasks), len(unicode_titles))


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTask))
    suite.addTests(loader.loadTestsFromTestCase(TestStorageManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTodoCLI))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())