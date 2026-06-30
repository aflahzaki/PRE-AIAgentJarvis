# J.A.R.V.I.S Telegram Bot Interface

A Telegram bot frontend for the J.A.R.V.I.S AI assistant system. Allows you to interact with all J.A.R.V.I.S capabilities through Telegram messages.

## Prerequisites

- Python 3.11+
- `python-telegram-bot` >= 20.0 (already in requirements_v2.txt)
- A Telegram Bot Token from BotFather
- J.A.R.V.I.S core system configured (providers, database, etc.)

## Setup Guide

### 1. Create a Telegram Bot via BotFather

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` to create a new bot
3. Follow the prompts to set a name and username
4. BotFather will provide a **Bot Token** (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
5. Save this token securely

### 2. Get Your Telegram User ID

1. Search for `@userinfobot` on Telegram
2. Send any message to it
3. It will reply with your user ID (a number like `123456789`)
4. Note this for the allowed users configuration

### 3. Configure Environment Variables

Add the following to your `.env` file in the `J.A.R.V.I.S_system/` directory:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ALLOWED_USERS=your_user_id_here
```

For multiple allowed users, separate IDs with commas:

```env
TELEGRAM_ALLOWED_USERS=123456789,987654321
```

### 4. Run the Bot

From the `J.A.R.V.I.S_system/` directory:

```bash
python run_telegram.py
```

Or from the project root:

```bash
python J.A.R.V.I.S_system/run_telegram.py
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and introduction |
| `/help` | Show all available commands |
| `/status` | Show system status (providers, memory) |
| `/tasks` | List today's scheduled tasks |
| `/addtask <title>` | Add a new task |
| `/journal` | Start a journal entry |
| `/search <query>` | Search the web via AI |

Any other text message will be processed through the J.A.R.V.I.S orchestrator, which routes it to the appropriate AI agent (coder, researcher, web search, etc.).

## Security

The bot uses a user whitelist for access control:

- Only user IDs listed in `TELEGRAM_ALLOWED_USERS` can interact with the bot
- Unauthorized users receive an "Access denied" message
- If `TELEGRAM_ALLOWED_USERS` is empty or not set, all users are denied

## Architecture

```
Telegram User
    |
    v
TelegramBot (bot.py)
    |
    v
Handlers (handlers.py)
    |
    v
Orchestrator (core/orchestrator.py)
    |
    +---> CoderAgent
    +---> ResearcherAgent
    +---> WebSearchAgent
    +---> SchedulerAgent
    +---> WriterAgent
    +---> ...
```

## Troubleshooting

- **"TELEGRAM_BOT_TOKEN not set"**: Ensure your `.env` file has the token and `load_dotenv()` is called
- **"Access denied"**: Add your Telegram user ID to `TELEGRAM_ALLOWED_USERS`
- **Bot not responding**: Check that at least one LLM provider (Ollama/Groq) is available
- **Import errors**: Run `pip install -r requirements_v2.txt` to install dependencies
