# CLI Todo App

A simple, lightweight command-line todo list manager written in Python. No external dependencies required—just Python 3.7+ and you're ready to go!

## Features

✨ **Simple & Fast**: Single-file application with intuitive commands  
💾 **Persistent Storage**: Todos saved to `~/.todo.json` across sessions  
🔒 **Atomic Writes**: Safe file operations prevent data corruption  
🎯 **Zero Dependencies**: Uses only Python standard library  
🌍 **Cross-Platform**: Works on Windows, macOS, and Linux  

## Requirements

- Python 3.7 or higher
- No external dependencies

## Installation

1. **Download the script:**
   ```bash
   curl -O https://raw.githubusercontent.com/gianfranco-omnigpt/cli-todo-app/main/todo.py
   ```

2. **Make it executable (Unix/macOS):**
   ```bash
   chmod +x todo.py
   ```

3. **Optional: Add to PATH for global access:**
   ```bash
   # Move to a directory in your PATH
   sudo mv todo.py /usr/local/bin/todo
   
   # Or create a symlink
   ln -s $(pwd)/todo.py /usr/local/bin/todo
   ```

## Usage

### Add a Todo

Create a new todo item:

```bash
python todo.py add "Buy groceries"
# ✓ Added todo #1: Buy groceries

python todo.py add "Walk the dog"
# ✓ Added todo #2: Walk the dog

python todo.py add "Finish project report"
# ✓ Added todo #3: Finish project report
```

### List All Todos

View all your todos:

```bash
python todo.py list
# [ ] 1. Buy groceries
# [ ] 2. Walk the dog
# [ ] 3. Finish project report
```

Empty list:
```bash
python todo.py list
# No todos yet. Add one with: todo.py add "Your task"
```

### Complete a Todo

Mark a todo as done:

```bash
python todo.py complete 1
# ✓ Completed todo #1

python todo.py list
# [✓] 1. Buy groceries
# [ ] 2. Walk the dog
# [ ] 3. Finish project report
```

### Delete a Todo

Remove a todo:

```bash
python todo.py delete 2
# ✓ Deleted todo #2

python todo.py list
# [✓] 1. Buy groceries
# [ ] 3. Finish project report
```

### Get Help

View available commands:

```bash
python todo.py --help
# Shows all available commands and options

python todo.py add --help
# Shows help for the 'add' command
```

### Check Version

```bash
python todo.py --version
# todo 1.0.0
```

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `add <description>` | Create a new todo | `python todo.py add "Task description"` |
| `list` | Show all todos | `python todo.py list` |
| `complete <id>` | Mark todo as done | `python todo.py complete 1` |
| `delete <id>` | Remove a todo | `python todo.py delete 1` |
| `--help` | Show help message | `python todo.py --help` |
| `--version` | Show version | `python todo.py --version` |

## Storage

Todos are stored in a JSON file located at:
- **Unix/macOS**: `~/.todo.json`
- **Windows**: `C:\Users\<YourUsername>\.todo.json`

### Storage Format

```json
{
  "todos": [
    {
      "id": 1,
      "description": "Buy groceries",
      "completed": false,
      "created_at": "2025-01-20T10:30:00.123456"
    }
  ],
  "next_id": 2
}
```

### Backup Your Todos

```bash
# Create a backup
cp ~/.todo.json ~/.todo.json.backup

# Restore from backup
cp ~/.todo.json.backup ~/.todo.json
```

## Error Handling

The application provides helpful error messages for common issues:

### Invalid Todo ID
```bash
python todo.py complete 999
# ✗ Todo #999 not found
```

### Empty Description
```bash
python todo.py add ""
# ✗ Todo description cannot be empty
```

### Negative ID
```bash
python todo.py delete -1
# ✗ Error: Todo ID must be non-negative
```

### Corrupted Storage File
```
Error: Storage file is corrupted at /home/user/.todo.json
Details: Expecting value: line 1 column 1 (char 0)
Please fix or delete the file to continue.
```

## Troubleshooting

### Python Version Error

**Problem**: `Error: This application requires Python 3.7 or higher`

**Solution**: Upgrade Python:
```bash
# Check your Python version
python3 --version

# Use python3 explicitly
python3 todo.py list
```

### Permission Denied

**Problem**: Cannot write to storage file

**Solution**: Check file permissions:
```bash
# View permissions
ls -la ~/.todo.json

# Fix permissions
chmod 600 ~/.todo.json
```

### Storage File Corrupted

**Problem**: JSON decode error when running commands

**Solution**: 
1. Backup the file: `cp ~/.todo.json ~/.todo.json.backup`
2. Delete the corrupted file: `rm ~/.todo.json`
3. Run any command to recreate: `python todo.py list`

### Command Not Found (after installing to PATH)

**Problem**: `todo: command not found`

**Solution**:
```bash
# Make sure the file is executable
chmod +x /usr/local/bin/todo

# Verify it's in PATH
which todo

# Check PATH includes the directory
echo $PATH
```

## Development

### Project Structure

```
todo.py (single file, ~390 lines)
├── Todo (dataclass) - Data model
├── TodoStorage (class) - JSON persistence
├── TodoManager (class) - Business logic
├── TodoCLI (class) - Command-line interface
└── main() - Entry point
```

### Running Tests

Manual testing checklist:

```bash
# Test adding todos
python todo.py add "Test task 1"
python todo.py add "Test task 2"
python todo.py add "Task with special chars: @#$%"

# Test listing
python todo.py list

# Test completing
python todo.py complete 1

# Test deleting
python todo.py delete 2

# Test error cases
python todo.py complete 999  # Non-existent ID
python todo.py add ""        # Empty description
python todo.py delete -1     # Negative ID

# Test edge cases
python todo.py add "Very long description..." # 1000+ characters
```

### Code Quality

- **Type hints**: All functions have type annotations
- **Docstrings**: Comprehensive documentation for all classes and methods
- **Error handling**: Graceful degradation with helpful error messages
- **Atomic writes**: Temp file + rename pattern prevents corruption
- **Cross-platform**: Uses `pathlib` for path handling

## Architecture

The application follows a clean three-layer architecture:

1. **CLI Layer** (`TodoCLI`): Argument parsing and output formatting
2. **Business Logic Layer** (`TodoManager`): CRUD operations and validation
3. **Data Layer** (`TodoStorage`): JSON file persistence

### Design Decisions

- **JSON over SQLite**: Human-readable, easy to debug, sufficient for personal use
- **Auto-incrementing IDs**: Never reuse deleted IDs for simplicity
- **Home directory storage**: Predictable location, user-accessible
- **No configuration**: Zero-config philosophy with sensible defaults
- **Timestamps included**: Future-proof for sorting and analytics

## Limitations

- **Single user**: No multi-user support or authentication
- **No concurrency**: Running multiple instances simultaneously may cause conflicts
- **In-memory operations**: All todos loaded into memory (acceptable for personal use)
- **No undo**: Deletions are permanent (manual backup recommended)

## Future Enhancements

The architecture supports future additions:

- **Due dates**: Add `due_date` field to Todo model
- **Priorities**: Add `priority` field (1-5)
- **Categories/Tags**: Add `tags` field
- **Search**: Filter todos by keyword
- **Edit**: Update existing todo descriptions
- **Export**: Generate CSV or Markdown reports

## License

This is free and unencumbered software released into the public domain.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

For issues or questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review the storage file format for manual debugging

---

**Made with ❤️ using Python**