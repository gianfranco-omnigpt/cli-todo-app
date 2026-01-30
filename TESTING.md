# Testing Guide for CLI Todo App

This document provides a comprehensive testing guide for the CLI Todo App, including manual test cases, edge cases, and troubleshooting procedures.

## Prerequisites

- Python 3.7 or higher installed
- `todo.py` file downloaded and accessible
- Terminal/Command Prompt access

## Quick Test Suite

Run these commands in sequence to verify basic functionality:

```bash
# Clean slate - remove existing todos
rm ~/.todo.json 2>/dev/null || true

# Test 1: Add todos
python todo.py add "Buy groceries"
python todo.py add "Walk the dog"
python todo.py add "Finish project report"

# Test 2: List todos
python todo.py list
# Expected output:
# [ ] 1. Buy groceries
# [ ] 2. Walk the dog
# [ ] 3. Finish project report

# Test 3: Complete a todo
python todo.py complete 2
python todo.py list
# Expected: Todo #2 should show [✓]

# Test 4: Delete a todo
python todo.py delete 1
python todo.py list
# Expected: Only todos #2 and #3 should remain

# Test 5: Help command
python todo.py --help
python todo.py add --help

# Test 6: Version
python todo.py --version
```

## Detailed Test Cases

### 1. Basic CRUD Operations

#### Test 1.1: Add Single Todo
```bash
python todo.py add "Test task"
# Expected: ✓ Added todo #1: Test task
```

#### Test 1.2: Add Multiple Todos
```bash
python todo.py add "First task"
python todo.py add "Second task"
python todo.py add "Third task"
python todo.py list
# Expected: 3 todos listed with IDs 1, 2, 3
```

#### Test 1.3: List Empty Todos (First Run)
```bash
rm ~/.todo.json
python todo.py list
# Expected: No todos yet. Add one with: todo.py add "Your task"
```

#### Test 1.4: Complete Todo
```bash
python todo.py add "Task to complete"
python todo.py complete 1
python todo.py list
# Expected: [✓] 1. Task to complete
```

#### Test 1.5: Delete Todo
```bash
python todo.py add "Task to delete"
TODO_ID=$(python todo.py list | grep "Task to delete" | awk '{print $2}' | tr -d '.')
python todo.py delete $TODO_ID
python todo.py list
# Expected: Task should not appear in list
```

### 2. Error Handling Tests

#### Test 2.1: Empty Description
```bash
python todo.py add ""
# Expected: ✗ Todo description cannot be empty
# Exit code: 1
```

#### Test 2.2: Whitespace-Only Description
```bash
python todo.py add "   "
# Expected: ✗ Todo description cannot be empty
# Exit code: 1
```

#### Test 2.3: Non-Existent ID (Complete)
```bash
python todo.py complete 999
# Expected: ✗ Todo #999 not found
# Exit code: 1
```

#### Test 2.4: Non-Existent ID (Delete)
```bash
python todo.py delete 999
# Expected: ✗ Todo #999 not found
# Exit code: 1
```

#### Test 2.5: Negative ID (Complete)
```bash
python todo.py complete -1
# Expected: ✗ Error: Todo ID must be non-negative
# Exit code: 1
```

#### Test 2.6: Negative ID (Delete)
```bash
python todo.py delete -1
# Expected: ✗ Error: Todo ID must be non-negative
# Exit code: 1
```

### 3. Edge Cases

#### Test 3.1: Very Long Description
```bash
# Generate 1000+ character string
python todo.py add "$(python -c 'print("A" * 1500)')"
# Expected: ✗ Todo description is too long (max 1000 characters)
```

#### Test 3.2: Special Characters
```bash
python todo.py add "Task with special chars: @#$%^&*()"
python todo.py add "Task with quotes: \"Hello World\""
python todo.py add "Task with emoji: 🎉 🚀 ✨"
python todo.py list
# Expected: All tasks should display correctly
```

#### Test 3.3: Unicode Characters
```bash
python todo.py add "Task in 中文"
python todo.py add "Task in العربية"
python todo.py add "Task in Русский"
python todo.py list
# Expected: All tasks should display correctly
```

#### Test 3.4: Newline in Description
```bash
python todo.py add "Task with
newline"
python todo.py list
# Expected: Should handle gracefully (may display as single line)
```

#### Test 3.5: Complete Already Completed Todo
```bash
python todo.py add "Task"
python todo.py complete 1
python todo.py complete 1
# Expected: ✓ Completed todo #1 (both times)
```

#### Test 3.6: Delete Completed Todo
```bash
python todo.py add "Task to complete then delete"
python todo.py complete 1
python todo.py delete 1
python todo.py list
# Expected: Todo should be removed
```

### 4. Persistence Tests

#### Test 4.1: Data Persists Between Runs
```bash
python todo.py add "Persistent task"
# Close terminal and open new one
python todo.py list
# Expected: Task should still be there
```

#### Test 4.2: Storage File Location
```bash
ls -la ~/.todo.json
# Expected: File exists in home directory
```

#### Test 4.3: Storage File Format
```bash
cat ~/.todo.json
# Expected: Valid JSON with "todos" and "next_id" fields
python -m json.tool ~/.todo.json
# Expected: Pretty-printed JSON without errors
```

### 5. File System Tests

#### Test 5.1: Corrupted Storage File
```bash
echo "invalid json {{{" > ~/.todo.json
python todo.py list
# Expected: Error message about corrupted file
# Should suggest file location for manual inspection
```

#### Test 5.2: Empty Storage File
```bash
echo "" > ~/.todo.json
python todo.py list
# Expected: Error message about corrupted/empty file
```

#### Test 5.3: Permission Denied (Unix/macOS)
```bash
touch ~/.todo.json
chmod 000 ~/.todo.json
python todo.py list
# Expected: Error about permission denied
# Cleanup: chmod 644 ~/.todo.json
```

#### Test 5.4: Storage File Recreation
```bash
rm ~/.todo.json
python todo.py list
ls -la ~/.todo.json
# Expected: File should be automatically created
```

### 6. Performance Tests

#### Test 6.1: Add 100 Todos
```bash
for i in {1..100}; do
  python todo.py add "Task $i"
done
python todo.py list | wc -l
# Expected: 100 lines (plus header if any)
```

#### Test 6.2: List Large Number of Todos
```bash
time python todo.py list
# Expected: Should complete in < 1 second
```

#### Test 6.3: Complete Multiple Todos
```bash
for i in {1..50}; do
  python todo.py complete $i
done
python todo.py list | grep "✓" | wc -l
# Expected: 50 completed todos
```

### 7. Command-Line Interface Tests

#### Test 7.1: No Command
```bash
python todo.py
# Expected: Help message displayed
# Exit code: 1
```

#### Test 7.2: Invalid Command
```bash
python todo.py invalid
# Expected: Error message or help
```

#### Test 7.3: Help for Each Command
```bash
python todo.py --help
python todo.py add --help
python todo.py list --help
python todo.py complete --help
python todo.py delete --help
# Expected: Helpful usage information for each
```

#### Test 7.4: Version Flag
```bash
python todo.py --version
# Expected: todo 1.0.0
```

### 8. Cross-Platform Tests

#### Test 8.1: Windows Path
```powershell
# On Windows
python todo.py add "Windows test"
dir %USERPROFILE%\.todo.json
# Expected: File exists in user profile directory
```

#### Test 8.2: macOS/Linux Path
```bash
# On macOS/Linux
python todo.py add "Unix test"
ls -la ~/.todo.json
# Expected: File exists in home directory
```

### 9. Concurrent Access Tests

#### Test 9.1: Rapid Sequential Operations
```bash
python todo.py add "Task 1" & python todo.py add "Task 2" & wait
python todo.py list
# Expected: Both tasks should be added (though order may vary)
# Note: Concurrent writes not officially supported
```

### 10. Stress Tests

#### Test 10.1: Maximum Description Length
```bash
python todo.py add "$(python -c 'print("A" * 1000)')"
# Expected: Should succeed (exactly 1000 chars)
```

#### Test 10.2: 1000+ Todos
```bash
for i in {1..1000}; do
  python todo.py add "Stress test task $i"
done
python todo.py list | tail -10
# Expected: Should handle gracefully, may be slow
```

## Automated Test Script

Save this as `test_todo.sh` for automated testing:

```bash
#!/bin/bash

# CLI Todo App Test Suite
# Run this script to automatically test the todo app

set -e  # Exit on error

echo "Starting CLI Todo App Test Suite..."
echo "===================================="

# Cleanup
rm -f ~/.todo.json

# Test 1: Add
echo "Test 1: Adding todos..."
python todo.py add "Test task 1" > /dev/null
python todo.py add "Test task 2" > /dev/null
echo "✓ Add test passed"

# Test 2: List
echo "Test 2: Listing todos..."
OUTPUT=$(python todo.py list)
if [[ $OUTPUT == *"Test task 1"* ]] && [[ $OUTPUT == *"Test task 2"* ]]; then
  echo "✓ List test passed"
else
  echo "✗ List test failed"
  exit 1
fi

# Test 3: Complete
echo "Test 3: Completing todo..."
python todo.py complete 1 > /dev/null
OUTPUT=$(python todo.py list)
if [[ $OUTPUT == *"[✓]"* ]]; then
  echo "✓ Complete test passed"
else
  echo "✗ Complete test failed"
  exit 1
fi

# Test 4: Delete
echo "Test 4: Deleting todo..."
python todo.py delete 2 > /dev/null
OUTPUT=$(python todo.py list)
if [[ $OUTPUT != *"Test task 2"* ]]; then
  echo "✓ Delete test passed"
else
  echo "✗ Delete test failed"
  exit 1
fi

# Test 5: Error handling
echo "Test 5: Error handling..."
python todo.py complete 999 2>&1 | grep -q "not found" && echo "✓ Error handling passed" || exit 1

# Test 6: Empty description
echo "Test 6: Empty description validation..."
python todo.py add "" 2>&1 | grep -q "cannot be empty" && echo "✓ Validation passed" || exit 1

echo "===================================="
echo "All tests passed! ✓"

# Cleanup
rm -f ~/.todo.json
```

## Troubleshooting Test Failures

### Issue: "command not found: python"
**Solution**: Use `python3` instead:
```bash
python3 todo.py list
```

### Issue: "No module named dataclasses"
**Solution**: Upgrade Python to 3.7+:
```bash
python --version  # Check version
# Upgrade Python as needed
```

### Issue: Tests fail due to existing todos
**Solution**: Clear the storage file before testing:
```bash
rm ~/.todo.json
```

### Issue: Permission denied errors
**Solution**: Check file permissions:
```bash
chmod 600 ~/.todo.json
```

### Issue: JSON decode errors
**Solution**: Validate or recreate the storage file:
```bash
# Validate
python -m json.tool ~/.todo.json

# Or recreate
rm ~/.todo.json
python todo.py list
```

## Test Coverage Summary

This test suite covers:

- ✅ All CRUD operations (Create, Read, Update, Delete)
- ✅ Error handling and validation
- ✅ Edge cases and boundary conditions
- ✅ File system operations
- ✅ Data persistence
- ✅ Cross-platform compatibility
- ✅ Performance with large datasets
- ✅ Command-line interface
- ✅ Unicode and special characters

## Reporting Issues

If you find any failing tests:

1. Note the exact command that failed
2. Record the error message
3. Check Python version: `python --version`
4. Check storage file: `cat ~/.todo.json`
5. Open an issue on GitHub with details

## Continuous Testing

For ongoing development, run the test suite regularly:

```bash
# Quick smoke test
bash test_todo.sh

# Manual verification
python todo.py add "Test" && python todo.py list && python todo.py delete 1

# Check storage integrity
python -m json.tool ~/.todo.json
```

---

**Happy Testing! 🧪**