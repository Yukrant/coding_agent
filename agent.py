from llm import chat_with_gemini
import re
import os
import json
import shutil
import datetime
from executor import run_command, get_system_info, list_directory
from utils import write_file, read_file, ensure_dir, copy_file

# Initialize conversation history
conversation_history = []
history_file = "conversation_history.json"

# Command aliases for more intuitive usage
COMMAND_ALIASES = {
    # Main command mapping
    "help": "!help",
    "init": "!init",
    "run": "!run",
    "list": "!list",
    "dir": "!dir",
    "ls": "!dir",
    "read": "!read",
    "cat": "!read",
    "create": "!create",
    "delete": "!delete",
    "rm": "!delete",
    "deleteall": "!deleteall",
    "clean": "!deleteall",
    "history": "!history",
    "info": "!info",
    "system": "!info",
    
    # Additional aliases for flexibility
    "new": "!init",
    "make": "!init",
    "setup": "!init",
    "execute": "!run",
    "show": "!read",
    "view": "!read",
    "write": "!create",
    "touch": "!create",
    "remove": "!delete",
    "purge": "!deleteall",
}

def display_welcome():
    """Display welcome message and command help."""
    welcome = """
🤖 Gemini AI Agent 🤖
-----------------------
This agent helps you generate and manage code using Google's Gemini AI.

Key Features:
• Create code with AI assistance
• Save code with proper file extensions
• Manage files (create, read, delete)
• Initialize project structures
• Execute commands
• Track conversation history
    
Type 'help' for a list of available commands.
-----------------------
"""
    print(welcome)

def save_history(prompt, response, files=None):
    """Save conversation to history."""
    global conversation_history
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "prompt": prompt,
        "response": response[:500] + ("..." if len(response) > 500 else ""),  # Truncate long responses
        "files_created": files or []
    }
    
    conversation_history.append(entry)
    
    # Save to file
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, indent=2)
    except Exception as e:
        print(f"❌ Error saving history: {str(e)}")

def load_history():
    """Load conversation history from file."""
    global conversation_history
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                conversation_history = json.load(f)
        except Exception as e:
            print(f"❌ Error loading history: {str(e)}")
            conversation_history = []
    else:
        conversation_history = []

def show_history(limit=10):
    """Display the conversation history."""
    if not conversation_history:
        return "No conversation history available."
    
    # Show the most recent conversations first, limited by the parameter
    recent = conversation_history[-limit:] if limit else conversation_history
    
    result = []
    for i, entry in enumerate(recent):
        files_str = ", ".join(entry["files_created"]) if entry["files_created"] else "None"
        result.append(f"{i+1}. [{entry['timestamp']}] 👤: {entry['prompt']}\n   🤖: {entry['response']}\n   📄 Files: {files_str}")
    
    return "\n\n".join(result)

def save_code_blocks(text):
    """Extract and save code blocks with proper file extensions."""
    os.makedirs("generated", exist_ok=True)
    
    # Improved regex to capture language/extension info
    blocks = re.findall(r"```(\w*)\n(.*?)```", text, re.DOTALL)
    saved_files = []
    
    if blocks:
        print("\n📂 Save generated code:")
        print("   1. Default directory (generated/)")
        print("   2. Custom directory")
        target_choice = input("Select option [1]: ").strip()
        
        if target_choice == "2":
            target_dir = input("Enter target directory: ").strip()
            if not target_dir:
                target_dir = "generated"
        else:
            target_dir = "generated"
        
        # Ask if we should create project structure
        print("\n🏗️  Project structure:")
        print("   y - Organize files in appropriate folders")
        print("   n - Save all files in the target directory")
        create_structure = input("Organize files? (y/n) [n]: ").lower().strip()
        create_structure = create_structure == 'y'
        
        ensure_dir(target_dir)
        
        for i, (lang, content) in enumerate(blocks):
            # Map common language names to file extensions
            extension_map = {
                "python": "py", "py": "py",
                "javascript": "js", "js": "js",
                "jsx": "jsx",
                "typescript": "ts", "ts": "ts",
                "tsx": "tsx",
                "html": "html",
                "css": "css",
                "java": "java",
                "cpp": "cpp", "c++": "cpp",
                "c": "c",
                "json": "json",
                "bash": "sh", "shell": "sh",
                "": "txt"  # Default to .txt if no language specified
            }
            
            ext = extension_map.get(lang.lower(), "txt")
            
            # Try to extract file path from code block content or comments
            file_path = None
            
            if create_structure:
                # Look for file path indicators in content
                path_match = re.search(r'(?:\/\/|#|\/\*)\s*(?:file|path):\s*([^\n\r]*)', content)
                if path_match:
                    file_path = path_match.group(1).strip()
                
                # Check for common file patterns
                elif lang.lower() in ["js", "javascript"] and "import React" in content and "export default" in content:
                    file_path = "components/Component" + str(i+1) + ".jsx"
                elif "package.json" in content and '"dependencies"' in content:
                    file_path = "package.json"
                elif lang.lower() in ["html"] and "<html" in content:
                    file_path = "public/index.html"
                elif lang.lower() in ["css"] and "{" in content:
                    file_path = "styles/style.css"
                elif lang.lower() in ["bash", "sh"] and ("npm" in content or "npx" in content):
                    file_path = "scripts/setup.sh"
            
            if file_path:
                # Make sure parent directory exists
                full_path = os.path.join(target_dir, file_path)
                parent_dir = os.path.dirname(full_path)
                ensure_dir(parent_dir)
                path = full_path
            else:
                # Default filename if no structure detected
                filename = f"file_{i+1}.{ext}"
                path = os.path.join(target_dir, filename)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            
            saved_files.append(path)
            print(f"💾 Saved: {path}")
    
    return saved_files

def is_safe_path(path):
    """Check if a file path is safe (no path traversal)."""
    # Normalize the path to prevent path traversal attacks
    normalized_path = os.path.normpath(path)
    
    # Check for suspicious path components
    if any(part in normalized_path for part in ['..', '~']):
        return False
    
    # Check if the path is absolute and outside the workspace
    if os.path.isabs(normalized_path):
        # Convert to absolute path and check if it's within our workspace
        workspace_dir = os.path.abspath(os.getcwd())
        abs_path = os.path.abspath(normalized_path)
        if not abs_path.startswith(workspace_dir):
            return False
    
    return True

def is_safe_command(command):
    """Check if a shell command is safe to run."""
    # List of dangerous commands to block
    dangerous_cmds = ['rm -rf', 'format', 'mkfs', 'dd', 'wget', 'curl', '>>', '>', '|']
    
    # Check for dangerous commands
    for cmd in dangerous_cmds:
        if cmd in command:
            return False
    
    return True

def delete_file(path):
    """Delete a file and return success/failure message."""
    if not is_safe_path(path):
        return f"❌ Security error: Invalid file path: {path}"
    
    try:
        if os.path.exists(path):
            os.remove(path)
            return f"✅ Deleted: {path}"
        else:
            return f"❌ File not found: {path}"
    except Exception as e:
        return f"❌ Error deleting {path}: {str(e)}"

def list_generated_files():
    """List all files in the generated directory."""
    if not os.path.exists("generated"):
        return "No generated files found."
    
    files = os.listdir("generated")
    if not files:
        return "No generated files found."
    
    return "\n".join([f"{i+1}. {file}" for i, file in enumerate(files)])

def create_custom_file(filename, content):
    """Create a file with custom name and content."""
    if not is_safe_path(filename):
        return f"❌ Security error: Invalid file path: {filename}"
    
    if not os.path.dirname(filename):
        # If no directory specified, save to generated folder
        filename = os.path.join("generated", filename)
    
    success = write_file(filename, content)
    if success:
        return f"✅ Created: {filename}"
    else:
        return f"❌ Failed to create: {filename}"

def delete_all_files():
    """Delete all files in the generated directory."""
    try:
        if not os.path.exists("generated"):
            return "No generated directory found."
            
        files = os.listdir("generated")
        if not files:
            return "No files to delete."
            
        deleted = []
        for file in files:
            file_path = os.path.join("generated", file)
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted.append(file)
                
        if deleted:
            return f"✅ Deleted {len(deleted)} files: {', '.join(deleted)}"
        else:
            return "No files were deleted."
    except Exception as e:
        return f"❌ Error deleting files: {str(e)}"

def initialize_project(project_type, target_dir):
    """Initialize a project structure based on type."""
    if not target_dir:
        target_dir = "generated/project"
    
    # Ensure directory exists and is empty
    if os.path.exists(target_dir) and os.listdir(target_dir):
        overwrite = input(f"\n⚠️ Directory '{target_dir}' already exists and is not empty. Overwrite? (y/n) [n]: ").lower().strip()
        if overwrite != 'y':
            return "❌ Project initialization canceled."
    
    ensure_dir(target_dir)
    
    # Print initialization message
    print(f"\n🚀 Initializing {project_type} project in '{target_dir}'...")
    
    if project_type.lower() == "nextjs":
        # Create basic Next.js structure
        dirs = [
            "pages", 
            "pages/api", 
            "public", 
            "styles", 
            "components"
        ]
        files = {
            "pages/index.js": "export default function Home() {\n  return <div>Hello Next.js</div>;\n}",
            "pages/_app.js": "import '../styles/globals.css';\n\nexport default function MyApp({ Component, pageProps }) {\n  return <Component {...pageProps} />;\n}",
            "styles/globals.css": "html, body {\n  padding: 0;\n  margin: 0;\n  font-family: -apple-system, sans-serif;\n}",
            "package.json": '{\n  "name": "nextjs-app",\n  "version": "0.1.0",\n  "private": true,\n  "scripts": {\n    "dev": "next dev",\n    "build": "next build",\n    "start": "next start"\n  },\n  "dependencies": {\n    "next": "latest",\n    "react": "latest",\n    "react-dom": "latest"\n  }\n}'
        }
        
        # Create directories
        for dir_path in dirs:
            full_path = os.path.join(target_dir, dir_path)
            ensure_dir(full_path)
            print(f"  📁 Created directory: {dir_path}")
        
        # Create files
        for file_path, content in files.items():
            full_path = os.path.join(target_dir, file_path)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📄 Created file: {file_path}")
        
        return f"✅ Next.js project created successfully in '{target_dir}'.\n\nTo run the project:\n  cd {target_dir}\n  npm install\n  npm run dev"
    
    elif project_type.lower() == "react":
        # Create basic React structure
        dirs = [
            "public",
            "src",
            "src/components",
            "src/styles"
        ]
        files = {
            "public/index.html": '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="utf-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1" />\n  <title>React App</title>\n</head>\n<body>\n  <div id="root"></div>\n</body>\n</html>',
            "src/index.js": 'import React from "react";\nimport ReactDOM from "react-dom";\nimport App from "./App";\n\nReactDOM.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>,\n  document.getElementById("root")\n);',
            "src/App.js": 'import React from "react";\n\nfunction App() {\n  return (\n    <div className="App">\n      <h1>Hello React</h1>\n    </div>\n  );\n}\n\nexport default App;',
            "package.json": '{\n  "name": "react-app",\n  "version": "0.1.0",\n  "private": true,\n  "dependencies": {\n    "react": "^18.2.0",\n    "react-dom": "^18.2.0"\n  },\n  "scripts": {\n    "start": "react-scripts start",\n    "build": "react-scripts build"\n  }\n}'
        }
        
        # Create directories
        for dir_path in dirs:
            full_path = os.path.join(target_dir, dir_path)
            ensure_dir(full_path)
            print(f"  📁 Created directory: {dir_path}")
        
        # Create files
        for file_path, content in files.items():
            full_path = os.path.join(target_dir, file_path)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📄 Created file: {file_path}")
        
        return f"✅ React project created successfully in '{target_dir}'.\n\nTo run the project:\n  cd {target_dir}\n  npm install\n  npm start"
    
    else:
        return f"❌ Unknown project type: {project_type}. Supported types: nextjs, react"

def process_command(command):
    """Process special commands with or without the ! prefix."""
    # Check if command is an alias and convert to standard form
    words = command.split()
    first_word = words[0].lower()
    
    # Handle commands without ! prefix using aliases
    if first_word in COMMAND_ALIASES:
        command = COMMAND_ALIASES[first_word] + command[len(first_word):]
    
    # History commands
    if command == "!help" or command == "!h" or command == "help":
        return """Available commands:
📁 File Management:
  !list (or list) - List all generated files
  !delete <filename> (or delete, rm) - Delete a file
  !deleteall (or deleteall, clean) - Delete all generated files
  !read <filename> (or read, cat) - Read a file's contents
  !create <filename>:<content> (or create, write) - Create a custom file
  !dir [path] (or dir, ls) - List files in a directory

🏗️ Project Management:
  !init <project_type> [target_dir] (or init, new, setup) - Initialize project structure
  Types: nextjs, react

🔧 System Commands:
  !run <command> (or run, execute) - Run a shell command
  !info (or info, system) - Show system information

📝 History:
  !history [limit] (or history) - Show conversation history

❓ Help:
  !help (or help, h) - Show this help message
  
💬 AI Interaction:
  Just type your question or request to interact with the AI

Type 'exit' to quit the agent"""
    
    elif command == "!history" or command.startswith("!history "):
        limit_str = command[9:].strip() if command.startswith("!history ") else ""
        try:
            limit = int(limit_str) if limit_str else 10
            return show_history(limit)
        except ValueError:
            return "❌ Invalid format. Use: !history <number>"
    
    # File operations
    elif command.startswith("!delete "):
        file_to_delete = command[8:].strip()
        if not os.path.dirname(file_to_delete):  # If no directory specified
            file_to_delete = os.path.join("generated", file_to_delete)
        return delete_file(file_to_delete)
    
    elif command == "!deleteall":
        return delete_all_files()
    
    elif command == "!list":
        return list_generated_files()
    
    elif command.startswith("!dir ") or command == "!dir":
        path = command[5:].strip() if command != "!dir" else "."
        return list_directory(path)
    
    elif command.startswith("!read "):
        file_to_read = command[6:].strip()
        if not os.path.dirname(file_to_read):  # If no directory specified
            file_to_read = os.path.join("generated", file_to_read)
        content = read_file(file_to_read)
        if content is not None:
            return f"📄 Contents of {file_to_read}:\n\n{content}"
        else:
            return f"❌ Could not read: {file_to_read}"
    
    elif command.startswith("!create "):
        # Format: !create filename:content
        parts = command[8:].split(":", 1)
        if len(parts) != 2:
            return "❌ Invalid format. Use: !create filename:content"
        filename, content = parts
        return create_custom_file(filename.strip(), content)
    
    elif command.startswith("!init ") or command == "!init":
        if command == "!init":
            # Interactive mode
            print("\n🏗️  Initialize new project:")
            print("   1. Next.js project")
            print("   2. React project")
            print("   3. Cancel")
            
            choice = input("Select project type [3]: ").strip()
            
            if choice == "1":
                project_type = "nextjs"
            elif choice == "2":
                project_type = "react"
            else:
                return "Project initialization canceled."
                
            target_dir = input("\nProject directory [generated/project]: ").strip()
            if not target_dir:
                target_dir = "generated/project"
                
            return initialize_project(project_type, target_dir)
        else:
            # Command mode: !init project_type [target_dir]
            parts = command[6:].strip().split(" ", 1)
            project_type = parts[0]
            target_dir = parts[1] if len(parts) > 1 else ""
            return initialize_project(project_type, target_dir)
    
    # System commands
    elif command.startswith("!run "):
        cmd = command[5:].strip()
        if not is_safe_command(cmd):
            return "❌ Security error: This command is not allowed for security reasons."
        return run_command(cmd)
    
    elif command == "!info":
        info = get_system_info()
        return json.dumps(info, indent=2)
    
    return None  # Not a special command

def check_environment():
    """Check if the environment is properly set up."""
    issues = []
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        issues.append("⚠️ GOOGLE_API_KEY not found in environment variables")
    
    # Create necessary directories
    try:
        ensure_dir("generated")
    except Exception as e:
        issues.append(f"⚠️ Couldn't create generated directory: {str(e)}")
    
    return issues

def main():
    # Display welcome message
    display_welcome()
    
    # Check environment
    issues = check_environment()
    if issues:
        print("⚠️ Environment Issues:")
        for issue in issues:
            print(f"  {issue}")
        print()
    
    # Ensure generated directory exists
    ensure_dir("generated")
    
    # Load conversation history
    load_history()
    
    while True:
        prompt = input("👤 > ")
        
        if prompt.lower() == "exit":
            print("Goodbye! 👋")
            break
        
        # Check for special commands
        result = process_command(prompt)
        if result:
            print(f"\n🤖 > {result}")
            continue
        
        # Normal LLM interaction
        try:
            reply = chat_with_gemini(prompt)
            print(f"\n🤖 > {reply}")
            saved_files = save_code_blocks(reply)
            
            # Save to history
            save_history(prompt, reply, saved_files)
        except Exception as e:
            error_msg = f"Error communicating with AI: {str(e)}"
            print(f"\n❌ {error_msg}")
            save_history(prompt, error_msg, [])

if __name__ == "__main__":
    main()
