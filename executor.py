import subprocess
import os
import platform

def run_command(command, capture_output=True):
    """Run a shell command and return the output.
    
    Args:
        command: The command to execute
        capture_output: Whether to capture and return output
    
    Returns:
        Command output or status message
    """
    try:
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            return result.stdout
        else:
            # Just run without capturing (for interactive commands)
            subprocess.run(command, shell=True, check=False)
            return "Command executed."
    except subprocess.CalledProcessError as e:
        return f"Error (exit code {e.returncode}):\n{e.stderr}"
    except Exception as e:
        return f"Failed to run command: {str(e)}"

def get_system_info():
    """Get basic system information."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "path": os.getcwd()
    }

def list_directory(path="."):
    """List files in the specified directory."""
    try:
        files = os.listdir(path)
        result = []
        for file in files:
            full_path = os.path.join(path, file)
            if os.path.isdir(full_path):
                result.append(f"📁 {file}/")
            else:
                size = os.path.getsize(full_path)
                size_str = f"{size} B"
                if size > 1024:
                    size_str = f"{size / 1024:.1f} KB"
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                result.append(f"📄 {file} ({size_str})")
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"
