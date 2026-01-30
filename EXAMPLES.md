# CLI Todo Application - Usage Examples

This guide provides practical examples for using the CLI todo application.

## Basic Usage

### Adding Tasks

```bash
# Simple task
todo add "Buy groceries"

# Task with details
todo add "Complete project proposal by Friday"

# Multiple tasks
todo add "Morning standup meeting"
todo add "Review pull requests"
todo add "Update documentation"
```

**Output:**
```
✓ Added task: Buy groceries
  ID: a1b2c3d4
```

### Listing Tasks

```bash
# List pending tasks (default)
todo list
```

**Output:**
```
Pending Tasks (3):

○ [a1b2c3d4] Buy groceries
○ [e5f6g7h8] Complete project proposal by Friday
○ [i9j0k1l2] Morning standup meeting
```

```bash
# List all tasks (pending + completed)
todo list --all
```

**Output:**
```
All Tasks (5):

○ [a1b2c3d4] Buy groceries
✓ [m3n4o5p6] Review pull requests
  Completed: 2025-01-23 14:30
○ [e5f6g7h8] Complete project proposal by Friday
✓ [q7r8s9t0] Update documentation
  Completed: 2025-01-23 15:45
○ [i9j0k1l2] Morning standup meeting
```

```bash
# List only completed tasks
todo list --completed
```

**Output:**
```
Completed Tasks (2):

✓ [m3n4o5p6] Review pull requests
  Completed: 2025-01-23 14:30
✓ [q7r8s9t0] Update documentation
  Completed: 2025-01-23 15:45
```

### Completing Tasks

```bash
# Complete using full ID
todo complete a1b2c3d4

# Complete using ID prefix (convenient!)
todo complete a1b2
todo complete e5f6
```

**Output:**
```
✓ Completed: Buy groceries
```

### Deleting Tasks

```bash
# Delete using full ID
todo delete i9j0k1l2

# Delete using ID prefix
todo delete i9j0
```

**Output:**
```
✓ Deleted: Morning standup meeting
```

## Real-World Scenarios

### Daily Work Routine

```bash
# Morning: Plan your day
todo add "Check emails"
todo add "Team standup at 9:30am"
todo add "Work on feature X"
todo add "Code review for PR #123"
todo add "1:1 meeting with manager at 2pm"

# Check your task list
todo list

# Throughout the day: Complete tasks
todo complete check  # Matches "Check emails"
todo complete team   # Matches "Team standup"
todo complete work   # Matches "Work on feature X"

# End of day: Review progress
todo list --completed  # See what you accomplished
todo list              # See what's left for tomorrow
```

### Project Management

```bash
# Add project tasks
todo add "Design database schema"
todo add "Implement user authentication"
todo add "Write API documentation"
todo add "Set up CI/CD pipeline"
todo add "Deploy to staging environment"

# Work through tasks
todo list

# Complete as you go
todo complete design
todo complete impl

# Check remaining work
todo list
```

### Shopping List

```bash
# Create shopping list
todo add "Milk"
todo add "Bread"
todo add "Eggs"
todo add "Coffee"
todo add "Vegetables"

# At the store: Mark items as you pick them up
todo complete milk
todo complete bread

# Check what's left
todo list

# Later: Clean up completed items
todo list --completed  # Review what you bought
```

### Personal Goals

```bash
# Set weekly goals
todo add "Exercise 3 times this week"
todo add "Read 50 pages of book"
todo add "Learn Python decorators"
todo add "Organize home office"

# Track progress
todo list

# Complete goals
todo complete exer
todo complete read

# Review achievements
todo list --completed
```

## Advanced Usage

### Working with ID Prefixes

You don't need to type the full UUID. The app intelligently matches prefixes:

```bash
# Full ID
todo complete a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Short prefix (first 4-8 characters usually enough)
todo complete a1b2
todo complete a1b2c3d4

# Very short prefix (if unique)
todo complete a1
```

**Note:** If the prefix matches multiple tasks, you'll get an error:
```
Error: Ambiguous task ID 'a1'. Please provide more characters.
```

### Unicode Support

The app fully supports Unicode characters and emojis:

```bash
todo add "🎉 Plan birthday party"
todo add "📧 Respond to important email"
todo add "🏃 Go for a run"
todo add "学习中文"  # Learn Chinese
todo add "Купить продукты"  # Buy groceries (Russian)

todo list
```

**Output:**
```
Pending Tasks (5):

○ [a1b2c3d4] 🎉 Plan birthday party
○ [e5f6g7h8] 📧 Respond to important email
○ [i9j0k1l2] 🏃 Go for a run
○ [m3n4o5p6] 学习中文
○ [q7r8s9t0] Купить продукты
```

### Batch Operations

While there's no built-in batch operation, you can use shell loops:

```bash
# Complete multiple tasks
for id in a1b2 e5f6 i9j0; do
    todo complete $id
done

# Delete multiple tasks
for id in m3n4 q7r8; do
    todo delete $id
done
```

## Tips & Tricks

### 1. Use Descriptive Task Names

✅ Good:
```bash
todo add "Review PR #123: Add user authentication"
todo add "Bug fix: Fix login redirect issue"
```

❌ Avoid:
```bash
todo add "Review"
todo add "Fix bug"
```

### 2. Leverage ID Prefix Matching

Instead of copying the full ID, use just enough characters to be unique:

```bash
todo list  # Copy first 4-8 characters of the ID
todo complete a1b2  # Much easier than full UUID!
```

### 3. Regular Review

```bash
# Daily review
todo list --all  # See everything

# Weekly cleanup
todo list --completed  # Review accomplishments
# Delete old completed tasks if needed
```

### 4. Empty State

When you have no pending tasks:

```bash
todo list
```

**Output:**
```
No pending tasks. Great job! 🎉
```

### 5. Data Location

Your tasks are stored in:
```
~/.todo/tasks.json
~/.todo/tasks.json.backup  # Automatic backup
```

You can manually inspect or edit these files if needed (they're human-readable JSON).

## Error Handling Examples

### Empty Title

```bash
todo add ""
```

**Output:**
```
Error: Task title cannot be empty
```

### Title Too Long

```bash
todo add "$(python3 -c 'print("a" * 501)')"
```

**Output:**
```
Error: Task title cannot exceed 500 characters
```

### Task Not Found

```bash
todo complete nonexistent123
```

**Output:**
```
Error: Task not found: nonexistent123
```

### Already Completed

```bash
todo complete a1b2  # First time: success
todo complete a1b2  # Second time: error
```

**Output:**
```
Error: Task is already completed
```

### Ambiguous ID

```bash
# If you have tasks with IDs starting with 'a1'
todo complete a  # Too short
```

**Output:**
```
Error: Ambiguous task ID 'a'. Please provide more characters.
```

## Integration with Other Tools

### Shell Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
alias t='todo'
alias ta='todo add'
alias tl='todo list'
alias tc='todo complete'
alias td='todo delete'
alias tla='todo list --all'
```

Usage:
```bash
ta "New task"  # Add task
tl             # List tasks
tc a1b2        # Complete task
```

### Git Hooks

Add tasks automatically on certain Git events:

```bash
# .git/hooks/post-commit
#!/bin/bash
todo add "Review commit $(git rev-parse --short HEAD)"
```

### Cron Jobs

Daily reminder to check tasks:

```bash
# Add to crontab: crontab -e
0 9 * * * todo list
```

## Troubleshooting

### Command Not Found

```bash
todo list
# bash: todo: command not found
```

**Solution:** The installation directory is not in your PATH. Either:
1. Use the full path: `/usr/local/bin/todo list`
2. Add to PATH: `export PATH="$HOME/bin:$PATH"`
3. Reinstall using the install script

### Permission Denied

```bash
todo list
# bash: /usr/local/bin/todo: Permission denied
```

**Solution:** Make the file executable:
```bash
chmod +x /usr/local/bin/todo
```

### Corrupted Data File

```bash
todo list
# Error: JSON file corrupted: ...
# Attempting to recover from backup...
# Successfully recovered from backup!
```

The app automatically recovers from backup. If that fails:

```bash
# Manually restore
cp ~/.todo/tasks.json.backup ~/.todo/tasks.json

# Or start fresh
rm ~/.todo/tasks.json
todo list  # Creates new empty file
```

## Getting Help

```bash
# General help
todo --help

# Command-specific help
todo add --help
todo list --help
todo complete --help
todo delete --help
```

---

**Happy task managing! 🎯**
