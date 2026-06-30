#!/usr/bin/env python3
"""
J.A.R.V.I.S - First Time Setup Wizard

Interactive setup wizard that guides users through configuring J.A.R.V.I.S
from scratch. Uses Rich library for beautiful terminal output with a
plain-text fallback if Rich is not yet installed.

Usage:
    python setup_jarvis.py

Features:
    - System check (Python, OS, RAM)
    - Dependency installation
    - Ollama setup guidance
    - API key configuration
    - Database setup (MySQL/SQLite)
    - Provider connectivity testing
    - Idempotent (safe to re-run)
    - Graceful Ctrl+C handling
    - Cross-platform (Windows/Linux/macOS)
"""

import os
import platform
import shutil
import subprocess
import sys
import time

# Path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
ENV_EXAMPLE = os.path.join(SCRIPT_DIR, ".env.example")
REQUIREMENTS_FILE = os.path.join(SCRIPT_DIR, "requirements_v2.txt")

# Plain text fallback jika Rich belum terinstall
RICH_AVAILABLE = False
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    pass


# ============================================================
# Plain-text fallback console (ketika Rich belum terinstall)
# ============================================================

class PlainConsole:
    """Fallback console when Rich is not available."""

    def print(self, *args, **kwargs):
        """Print plain text, stripping Rich markup."""
        text = " ".join(str(a) for a in args)
        # Strip basic Rich markup tags
        import re
        text = re.sub(r'\[/?[^\]]*\]', '', text)
        print(text)

    def input(self, prompt=""):
        """Get input from user."""
        import re
        prompt = re.sub(r'\[/?[^\]]*\]', '', prompt)
        return input(prompt)


# Pilih console berdasarkan ketersediaan Rich
if RICH_AVAILABLE:
    console = Console()
else:
    console = PlainConsole()


# ============================================================
# Utility Functions
# ============================================================

def get_ram_gb():
    """Get system RAM in GB. Returns None if cannot determine."""
    try:
        if platform.system() == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulong = ctypes.c_ulong
            class MEMORYSTATUS(ctypes.Structure):
                _fields_ = [
                    ('dwLength', c_ulong),
                    ('dwMemoryLoad', c_ulong),
                    ('dwTotalPhys', c_ulong),
                    ('dwAvailPhys', c_ulong),
                    ('dwTotalPageFile', c_ulong),
                    ('dwAvailPageFile', c_ulong),
                    ('dwTotalVirtual', c_ulong),
                    ('dwAvailVirtual', c_ulong),
                ]
            mem_status = MEMORYSTATUS()
            mem_status.dwLength = ctypes.sizeof(MEMORYSTATUS)
            kernel32.GlobalMemoryStatus(ctypes.byref(mem_status))
            return round(mem_status.dwTotalPhys / (1024 ** 3), 1)
        else:
            # Linux/macOS
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal'):
                        kb = int(line.split()[1])
                        return round(kb / (1024 ** 2), 1)
    except Exception:
        pass

    # Fallback: try psutil
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except ImportError:
        pass

    return None


def run_command(cmd, capture=True, timeout=120):
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str),
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", "Command not found"
    except Exception as e:
        return -1, "", str(e)


def load_env_file(path):
    """Load existing .env file into a dict. Returns empty dict if not found."""
    env_vars = {}
    if not os.path.exists(path):
        return env_vars
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, _, value = line.partition('=')
                    env_vars[key.strip()] = value.strip()
    except Exception:
        pass
    return env_vars


def save_env_file(path, env_vars, template_path=None):
    """Save env vars to .env file, preserving template structure."""
    lines = []
    if template_path and os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key, _, _ = stripped.partition('=')
                    key = key.strip()
                    if key in env_vars:
                        lines.append("{}={}\n".format(key, env_vars[key]))
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
    else:
        for key, value in env_vars.items():
            lines.append("{}={}\n".format(key, value))

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def print_step_header(step_num, total, title):
    """Print a step header."""
    if RICH_AVAILABLE:
        console.print()
        console.print(Panel(
            "[bold]Step {}/{}[/bold]: {}".format(step_num, total, title),
            border_style="cyan",
            padding=(0, 1),
        ))
    else:
        print("\n" + "=" * 50)
        print("  Step {}/{}: {}".format(step_num, total, title))
        print("=" * 50)


def print_success(msg):
    """Print a success message."""
    if RICH_AVAILABLE:
        console.print("  [green]\\u2713[/green] {}".format(msg))
    else:
        print("  [OK] {}".format(msg))


def print_warning(msg):
    """Print a warning message."""
    if RICH_AVAILABLE:
        console.print("  [yellow]\\u26a0[/yellow] {}".format(msg))
    else:
        print("  [!!] {}".format(msg))


def print_error(msg):
    """Print an error message."""
    if RICH_AVAILABLE:
        console.print("  [red]\\u2717[/red] {}".format(msg))
    else:
        print("  [FAIL] {}".format(msg))


def print_info(msg):
    """Print an info message."""
    if RICH_AVAILABLE:
        console.print("  [dim]{}[/dim]".format(msg))
    else:
        print("  {}".format(msg))


def ask_input(prompt_text, default="", password=False):
    """Ask user for input with optional default."""
    if default:
        display = "{} [{}]: ".format(prompt_text, default)
    else:
        display = "{}: ".format(prompt_text)

    if RICH_AVAILABLE:
        try:
            value = Prompt.ask(
                "  {}".format(prompt_text),
                default=default if default else None,
                password=password,
            )
        except (EOFError, KeyboardInterrupt):
            return default
    else:
        try:
            if password:
                import getpass
                value = getpass.getpass("  " + display)
            else:
                value = input("  " + display)
        except (EOFError, KeyboardInterrupt):
            return default

    return value if value else default


def ask_confirm(prompt_text, default=True):
    """Ask user for yes/no confirmation."""
    if RICH_AVAILABLE:
        try:
            return Confirm.ask("  {}".format(prompt_text), default=default)
        except (EOFError, KeyboardInterrupt):
            return default
    else:
        suffix = " [Y/n]: " if default else " [y/N]: "
        try:
            answer = input("  " + prompt_text + suffix).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return default
        if not answer:
            return default
        return answer in ('y', 'yes')


def ask_skip():
    """Ask user if they want to skip current step."""
    if RICH_AVAILABLE:
        console.print("  [dim]Press Enter to continue or 's' to skip[/dim]")
    else:
        print("  Press Enter to continue or 's' to skip")
    try:
        answer = input("  > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return True
    return answer == 's'


# ============================================================
# Step 1: System Check
# ============================================================

def step_system_check():
    """Check system requirements: Python version, OS, RAM."""
    print_step_header(1, 7, "System Check")

    # Python version
    py_version = "{}.{}.{}".format(
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )
    if sys.version_info >= (3, 8):
        print_success("Python {}".format(py_version))
    else:
        print_error(
            "Python {} (requires 3.8+)".format(py_version)
        )
        print_info("Please install Python 3.8 or newer from https://python.org")
        return False

    # OS detection
    os_name = platform.system()
    os_detail = platform.platform()
    print_success("OS: {} ({})".format(os_name, os_detail))

    # RAM check
    ram = get_ram_gb()
    if ram is not None:
        if ram >= 16:
            print_success("RAM: {}GB (sufficient for 7B models)".format(ram))
        elif ram >= 8:
            print_warning(
                "RAM: {}GB (minimum for 7B models, may be slow)".format(ram)
            )
        else:
            print_warning(
                "RAM: {}GB (insufficient for local models, use cloud providers)".format(ram)
            )
    else:
        print_info("RAM: Could not determine (not critical)")

    # pip check
    rc, stdout, _ = run_command([sys.executable, "-m", "pip", "--version"])
    if rc == 0:
        pip_ver = stdout.strip().split()[1] if stdout.strip() else "unknown"
        print_success("pip {} available".format(pip_ver))
    else:
        print_error("pip not available")
        print_info("Install pip: python -m ensurepip --upgrade")
        return False

    return True


# ============================================================
# Step 2: Install Dependencies
# ============================================================

def step_install_dependencies():
    """Install Python dependencies from requirements_v2.txt."""
    print_step_header(2, 7, "Install Dependencies")

    if not os.path.exists(REQUIREMENTS_FILE):
        print_error("requirements_v2.txt not found at: {}".format(REQUIREMENTS_FILE))
        return False

    if ask_skip():
        print_warning("Skipped dependency installation")
        return True

    print_info("Installing from requirements_v2.txt...")

    cmd = [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE, "-q"]
    rc, stdout, stderr = run_command(cmd, timeout=300)

    if rc == 0:
        print_success("All packages installed successfully")
        # Re-import Rich if it was just installed
        global RICH_AVAILABLE, console
        if not RICH_AVAILABLE:
            try:
                from rich.console import Console as RichConsole
                from rich.panel import Panel as RichPanel
                from rich.prompt import Prompt as RichPrompt, Confirm as RichConfirm
                RICH_AVAILABLE = True
                console = RichConsole()
                print_success("Rich library now available - output will be prettier!")
            except ImportError:
                pass
        return True
    else:
        print_error("Some packages failed to install")
        if stderr:
            # Show last few lines of error
            error_lines = stderr.strip().split('\n')[-5:]
            for line in error_lines:
                print_info("  {}".format(line))
        print_info("You can try manually: pip install -r requirements_v2.txt")
        return True  # Non-fatal, continue setup


# ============================================================
# Step 3: Ollama Setup
# ============================================================

def step_ollama_setup():
    """Check and guide Ollama installation."""
    print_step_header(3, 7, "Ollama Setup")

    # Check if ollama command exists
    ollama_cmd = shutil.which("ollama")
    if ollama_cmd is None:
        # Try running ollama --version anyway (might be in PATH but not found by which)
        rc, _, _ = run_command(["ollama", "--version"])
        if rc != 0:
            print_warning("Ollama not detected")
            print_info("Download from: https://ollama.ai")
            print_info("After installing, run: ollama pull qwen2.5-coder:7b")
            if ask_skip():
                print_warning("Skipped Ollama setup")
            return True

    # Ollama found, check if running
    print_success("Ollama installed")
    rc, stdout, _ = run_command(["ollama", "list"])
    if rc == 0:
        print_success("Ollama is running")
        if stdout.strip():
            models = [
                line.split()[0]
                for line in stdout.strip().split('\n')[1:]
                if line.strip()
            ]
            if models:
                print_info("Available models: {}".format(", ".join(models[:5])))
    else:
        print_warning("Ollama installed but not running")
        print_info("Start with: ollama serve")

    # Offer to pull recommended models
    print_info("")
    if ask_confirm("Download recommended model (qwen2.5-coder:7b)?", default=False):
        print_info("Pulling qwen2.5-coder:7b (this may take a while)...")
        rc, stdout, stderr = run_command(
            ["ollama", "pull", "qwen2.5-coder:7b"],
            capture=False,
            timeout=600,
        )
        if rc == 0:
            print_success("Model downloaded successfully")
        else:
            print_warning("Model download failed (you can try later: ollama pull qwen2.5-coder:7b)")

    return True


# ============================================================
# Step 4: API Keys Configuration
# ============================================================

def step_api_keys():
    """Configure API keys in .env file."""
    print_step_header(4, 7, "API Keys Configuration")

    # Load existing .env if present
    existing_env = load_env_file(ENV_FILE)
    if existing_env:
        print_info("Found existing .env file - will preserve existing values")
    else:
        print_info("Creating new .env file...")

    # Load template defaults
    template_env = load_env_file(ENV_EXAMPLE)
    env_vars = {**template_env, **existing_env}

    # --- Groq API Key ---
    print_info("")
    if RICH_AVAILABLE:
        console.print("  [bold]Groq API Key[/bold] (free from https://console.groq.com):")
    else:
        print("  Groq API Key (free from https://console.groq.com):")

    current_groq = env_vars.get("GROQ_API_KEY", "")
    if current_groq and current_groq != "your-groq-api-key-here":
        print_success("Groq key already configured ({}...{})".format(
            current_groq[:7], current_groq[-4:]
        ))
    else:
        groq_key = ask_input("Groq API Key (Enter to skip)")
        if groq_key:
            if groq_key.startswith("gsk_") and len(groq_key) > 20:
                env_vars["GROQ_API_KEY"] = groq_key
                print_success("Groq key saved")
            elif len(groq_key) > 10:
                # Accept anyway but warn
                env_vars["GROQ_API_KEY"] = groq_key
                print_warning("Key saved (unusual format, expected 'gsk_...')")
            else:
                print_warning("Key too short, skipped")
        else:
            print_warning("Skipped (can add later to .env)")

    # --- Gemini API Key ---
    print_info("")
    if RICH_AVAILABLE:
        console.print("  [bold]Google Gemini Key[/bold] (free from https://aistudio.google.com/apikey):")
    else:
        print("  Google Gemini Key (free from https://aistudio.google.com/apikey):")

    current_gemini = env_vars.get("GEMINI_API_KEY", "")
    if current_gemini and current_gemini != "your-gemini-api-key-here":
        print_success("Gemini key already configured ({}...{})".format(
            current_gemini[:7], current_gemini[-4:]
        ))
    else:
        gemini_key = ask_input("Gemini API Key (Enter to skip)")
        if gemini_key and len(gemini_key) > 10:
            env_vars["GEMINI_API_KEY"] = gemini_key
            print_success("Gemini key saved")
        elif gemini_key:
            print_warning("Key too short, skipped")
        else:
            print_warning("Skipped (can add later)")

    # --- OpenRouter API Key ---
    print_info("")
    if RICH_AVAILABLE:
        console.print("  [bold]OpenRouter Key[/bold] (free from https://openrouter.ai/keys):")
    else:
        print("  OpenRouter Key (free from https://openrouter.ai/keys):")

    current_or = env_vars.get("OPENROUTER_API_KEY", "")
    if current_or and current_or != "your-openrouter-api-key-here":
        print_success("OpenRouter key already configured ({}...{})".format(
            current_or[:7], current_or[-4:]
        ))
    else:
        or_key = ask_input("OpenRouter API Key (Enter to skip)")
        if or_key and len(or_key) > 10:
            env_vars["OPENROUTER_API_KEY"] = or_key
            print_success("OpenRouter key saved")
        elif or_key:
            print_warning("Key too short, skipped")
        else:
            print_warning("Skipped")

    # --- Telegram Bot Token ---
    print_info("")
    if RICH_AVAILABLE:
        console.print("  [bold]Telegram Bot Token[/bold] (from @BotFather on Telegram):")
    else:
        print("  Telegram Bot Token (from @BotFather on Telegram):")

    current_tg = env_vars.get("TELEGRAM_BOT_TOKEN", "")
    if current_tg and current_tg != "your-telegram-bot-token-here":
        print_success("Telegram token already configured")
    else:
        tg_token = ask_input("Telegram Bot Token (Enter to skip)")
        if tg_token and ":" in tg_token and len(tg_token) > 20:
            env_vars["TELEGRAM_BOT_TOKEN"] = tg_token
            print_success("Telegram token saved")
        elif tg_token:
            # Accept but warn
            env_vars["TELEGRAM_BOT_TOKEN"] = tg_token
            print_warning("Token saved (unusual format, expected 'NUMBER:STRING')")
        else:
            print_warning("Skipped")

    # Save .env file
    save_env_file(ENV_FILE, env_vars, ENV_EXAMPLE)
    print_info("")
    print_success("Configuration saved to .env")

    return env_vars


# ============================================================
# Step 5: Database Setup
# ============================================================

def step_database_setup(env_vars):
    """Configure and test database connection."""
    print_step_header(5, 7, "Database Setup")

    if ask_skip():
        print_warning("Skipped database setup (will use SQLite fallback)")
        env_vars["DB_FALLBACK_SQLITE"] = "true"
        save_env_file(ENV_FILE, env_vars, ENV_EXAMPLE)
        return env_vars

    # Ask MySQL or SQLite
    use_mysql = ask_confirm("Use MySQL/MariaDB? (No = SQLite)", default=True)

    if not use_mysql:
        env_vars["DB_FALLBACK_SQLITE"] = "true"
        save_env_file(ENV_FILE, env_vars, ENV_EXAMPLE)
        print_success("SQLite configured (data/jarvis.db)")

        # Try creating tables with SQLite
        _run_migrations(env_vars)
        return env_vars

    # MySQL configuration
    print_info("")
    db_host = ask_input("MySQL Host", default=env_vars.get("DB_HOST", "localhost"))
    db_port = ask_input("MySQL Port", default=env_vars.get("DB_PORT", "3306"))
    db_user = ask_input("MySQL Username", default=env_vars.get("DB_USER", "root"))
    db_pass = ask_input("MySQL Password", default=env_vars.get("DB_PASSWORD", ""), password=True)
    db_name = ask_input("Database Name", default=env_vars.get("DB_NAME", "jarvis_db"))

    env_vars["DB_HOST"] = db_host
    env_vars["DB_PORT"] = db_port
    env_vars["DB_USER"] = db_user
    env_vars["DB_PASSWORD"] = db_pass
    env_vars["DB_NAME"] = db_name
    env_vars["DB_FALLBACK_SQLITE"] = "true"  # Always enable fallback

    # Test MySQL connection
    print_info("Testing MySQL connection...")
    try:
        import pymysql as _pymysql
        conn = _pymysql.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_pass,
            connect_timeout=5,
        )
        # Try to create database if not exists
        with conn.cursor() as cur:
            cur.execute(
                "CREATE DATABASE IF NOT EXISTS `{}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(
                    db_name
                )
            )
        conn.close()
        print_success("MySQL connected! Database '{}' ready".format(db_name))
    except ImportError:
        print_warning("PyMySQL not installed - will use SQLite fallback")
        env_vars["DB_FALLBACK_SQLITE"] = "true"
    except Exception as e:
        print_error("MySQL connection failed: {}".format(str(e)))
        print_info("Will use SQLite fallback (DB_FALLBACK_SQLITE=true)")
        env_vars["DB_FALLBACK_SQLITE"] = "true"

    save_env_file(ENV_FILE, env_vars, ENV_EXAMPLE)

    # Run migrations
    _run_migrations(env_vars)

    return env_vars


def _run_migrations(env_vars):
    """Run database migrations to create tables."""
    print_info("Creating tables...")

    # Set environment variables for the migration
    for key, value in env_vars.items():
        os.environ[key] = value

    try:
        sys.path.insert(0, SCRIPT_DIR)
        from core.database.migrations import create_all_tables
        result = create_all_tables()
        if result.get("success"):
            created = result.get("created", [])
            existed = result.get("already_existed", [])
            total = len(created) + len(existed)
            if created:
                print_success("{} table(s) created".format(len(created)))
            if existed:
                print_info("{} table(s) already existed".format(len(existed)))
            if total == 0:
                print_success("Database ready ({})".format(result.get("db_type", "unknown")))
            else:
                print_success(
                    "{} total tables ready ({})".format(total, result.get("db_type", "unknown"))
                )
        else:
            print_warning(
                "Migration issue: {}".format(result.get("error", "unknown"))
            )
    except ImportError as e:
        print_warning("Cannot run migrations yet: {}".format(str(e)))
        print_info("Run migrations later: python -m core.database.migrations")
    except Exception as e:
        print_warning("Migration error: {}".format(str(e)))


# ============================================================
# Step 6: Test Providers
# ============================================================

def step_test_providers(env_vars):
    """Test connectivity to configured providers."""
    print_step_header(6, 7, "Test Providers")

    if ask_skip():
        print_warning("Skipped provider testing")
        return True

    # Set env vars for provider testing
    for key, value in env_vars.items():
        os.environ[key] = value

    available_count = 0

    # Test Ollama
    print_info("Testing Ollama...")
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from core.providers.ollama_provider import OllamaProvider
        ollama = OllamaProvider()
        if ollama.is_available():
            print_success("Ollama connected!")
            available_count += 1
        else:
            print_error("Ollama not running (start with: ollama serve)")
    except Exception as e:
        print_error("Ollama test failed: {}".format(str(e)))

    # Test Groq
    print_info("Testing Groq...")
    groq_key = env_vars.get("GROQ_API_KEY", "")
    if groq_key and groq_key != "your-groq-api-key-here":
        try:
            from core.providers.groq_provider import GroqProvider
            groq = GroqProvider(api_key=groq_key)
            if groq.is_available():
                model = env_vars.get("GROQ_MODEL", "llama-3.3-70b-versatile")
                print_success("Groq connected! (model: {})".format(model))
                available_count += 1
            else:
                print_error("Groq connection failed (check API key)")
        except Exception as e:
            print_error("Groq test failed: {}".format(str(e)))
    else:
        print_warning("Groq not configured")

    # Test Gemini
    print_info("Testing Gemini...")
    gemini_key = env_vars.get("GEMINI_API_KEY", "")
    if gemini_key and gemini_key != "your-gemini-api-key-here":
        try:
            from core.providers.gemini_provider import GeminiProvider
            gemini = GeminiProvider(api_key=gemini_key)
            if gemini.is_available():
                model = env_vars.get("GEMINI_MODEL", "gemini-2.0-flash")
                print_success("Gemini connected! (model: {})".format(model))
                available_count += 1
            else:
                print_error("Gemini connection failed (check API key)")
        except Exception as e:
            print_error("Gemini test failed: {}".format(str(e)))
    else:
        print_warning("Gemini not configured")

    # Test OpenRouter
    print_info("Testing OpenRouter...")
    or_key = env_vars.get("OPENROUTER_API_KEY", "")
    if or_key and or_key != "your-openrouter-api-key-here":
        try:
            from core.providers.openrouter_provider import OpenRouterProvider
            openrouter = OpenRouterProvider(api_key=or_key)
            if openrouter.is_available():
                model = env_vars.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
                print_success("OpenRouter connected! (model: {})".format(model))
                available_count += 1
            else:
                print_error("OpenRouter connection failed (check API key)")
        except Exception as e:
            print_error("OpenRouter test failed: {}".format(str(e)))
    else:
        print_warning("OpenRouter not configured")

    # Summary
    print_info("")
    if available_count > 0:
        print_success("At least {} provider(s) available!".format(available_count))
    else:
        print_warning("No providers available yet")
        print_info("Configure at least one API key or start Ollama to use J.A.R.V.I.S")

    return available_count > 0


# ============================================================
# Step 7: Complete
# ============================================================

def step_complete():
    """Show completion summary and start commands."""
    print_step_header(7, 7, "Setup Complete!")

    if RICH_AVAILABLE:
        completion_text = (
            "[bold green]J.A.R.V.I.S is ready![/bold green]\n\n"
            "[bold]Start commands:[/bold]\n"
            "  [cyan]python run_jarvis_v2.py[/cyan]  - Interactive REPL\n"
            "  [cyan]python run_web.py[/cyan]        - Web Dashboard\n"
            "  [cyan]python run_all.py[/cyan]        - All interfaces\n\n"
            "[dim]Configuration saved in .env\n"
            "Re-run this wizard anytime: python setup_jarvis.py[/dim]"
        )
        console.print()
        console.print(Panel(
            completion_text,
            title="[bold white]Ready[/bold white]",
            border_style="green",
            padding=(1, 2),
        ))
    else:
        print("")
        print("  +---------------------------------------+")
        print("  |  J.A.R.V.I.S is ready!               |")
        print("  |                                       |")
        print("  |  Start with: python run_jarvis_v2.py  |")
        print("  |  Web UI:     python run_web.py        |")
        print("  |  All:        python run_all.py        |")
        print("  +---------------------------------------+")
        print("")
        print("  Configuration saved in .env")
        print("  Re-run this wizard anytime: python setup_jarvis.py")

    # Offer to run J.A.R.V.I.S immediately
    print_info("")
    if ask_confirm("Start J.A.R.V.I.S now?", default=False):
        print_info("Starting J.A.R.V.I.S...")
        run_jarvis_path = os.path.join(SCRIPT_DIR, "run_jarvis_v2.py")
        os.execv(sys.executable, [sys.executable, run_jarvis_path])


# ============================================================
# Main Entry Point
# ============================================================

def print_banner():
    """Display the setup wizard welcome banner."""
    if RICH_AVAILABLE:
        banner_text = (
            "[bold cyan]J.A.R.V.I.S[/bold cyan] - First Time Setup Wizard\n\n"
            "[dim]This wizard will guide you through configuring J.A.R.V.I.S.\n"
            "You can skip any step and re-run this wizard later.\n"
            "Press Ctrl+C at any time to save progress and exit.[/dim]"
        )
        console.print()
        console.print(Panel(
            banner_text,
            title="[bold white]Setup[/bold white]",
            border_style="cyan",
            padding=(1, 2),
        ))
    else:
        print("")
        print("=" * 50)
        print("  J.A.R.V.I.S - First Time Setup Wizard")
        print("=" * 50)
        print("")
        print("  This wizard will guide you through configuring")
        print("  J.A.R.V.I.S. You can skip any step and re-run")
        print("  this wizard later.")
        print("  Press Ctrl+C at any time to save progress and exit.")
        print("")


def main():
    """Run the setup wizard."""
    try:
        print_banner()

        # Step 1: System Check
        if not step_system_check():
            print_error("System requirements not met. Please fix issues above.")
            sys.exit(1)

        # Step 2: Install Dependencies
        step_install_dependencies()

        # Step 3: Ollama Setup
        step_ollama_setup()

        # Step 4: API Keys
        env_vars = step_api_keys()

        # Step 5: Database Setup
        env_vars = step_database_setup(env_vars)

        # Step 6: Test Providers
        step_test_providers(env_vars)

        # Step 7: Complete
        step_complete()

    except KeyboardInterrupt:
        print_info("")
        print_info("")
        print_warning("Setup interrupted by user")
        # Save any .env progress
        if os.path.exists(ENV_FILE):
            print_info("Your .env configuration has been saved.")
        print_info("Re-run: python setup_jarvis.py")
        sys.exit(0)
    except Exception as e:
        print_error("Unexpected error: {}".format(str(e)))
        print_info("Please report this issue or try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
