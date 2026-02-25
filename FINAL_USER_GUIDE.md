# NERSC Multi-Source Q&A - User Guide

## 🎉 What You Get

Ask questions in natural language and automatically search **Google Docs AND Slack** - no need to specify sources!

## 🚀 For NERSC Users (After Deployment)

### One-Time Setup (2 minutes)

Authenticate with Google:

```bash
module load python/3.11
python /global/common/software/nersc/google-docs-qa/test_google_docs.py
```

**That's it!** Slack is already configured - no token needed!

### Daily Usage

**Just ask your question:**

```bash
module load python/3.11
/global/common/software/nersc/google-docs-qa/nersc-ask "What outages happened?"
```

Or use the full path:

```bash
python /global/common/software/nersc/google-docs-qa/multi_ask.py "Your question"
```

## 📝 Example Questions

```bash
# About incidents
nersc-ask "What outages happened in December?"

# About events
nersc-ask "What events are happening this week?"

# About Perlmutter
nersc-ask "What is the status of Perlmutter?"

# General questions
nersc-ask "Any maintenance scheduled?"
```

## 🤖 How It Works

When you ask a question, the system:

1. **Analyzes keywords** in your question
2. **Selects relevant sources** automatically:
   - Google Docs (downtimes, documentation, etc.)
   - Slack channels (#fire, #general, #hpcpoc, etc.)
3. **Searches all selected sources**
4. **Combines and presents results**

**You never need to specify which document or channel!**

## 🎯 Interactive Mode

Start an interactive session:

```bash
nersc-ask
```

Then ask multiple questions:

```
❓ Your question: What outages happened?
💡 Answer: ...

❓ Your question: Any events today?
💡 Answer: ...

❓ Your question: quit
```

## 🔧 What's Configured

### ✅ Google Docs (User Setup Required)
- You authenticate once with your Google account
- Can access any Google Doc you have permission to view

### ✅ Slack (Pre-Configured)
- Slack bot token configured centrally
- You don't need to do anything!
- Searches channels: #fire, #general, #hpcpoc, etc.

### ✅ AI-Powered Analysis (Optional)
For intelligent summaries and analysis:

```bash
export ANTHROPIC_API_KEY='your-key-here'
nersc-ask "Summarize all incidents"
```

Without API key: Uses keyword search (still works great!)

## 📊 Sources Searched

The system is configured to search:

**Google Docs:**
- NERSC Downtimes (Sept-Dec)
- *(More can be added by admins)*

**Slack Channels:**
- #fire - Incidents and outages
- #general - General announcements
- #hpcpoc - Perlmutter/HPC discussion
- *(More can be added by admins)*

## 🆘 Troubleshooting

### "First Time Google Authentication Required"
Run the one-time setup:
```bash
python /global/common/software/nersc/google-docs-qa/test_google_docs.py
```

### "Module not found"
Load Python:
```bash
module load python/3.11
```

### Not finding answers?
- Try rephrasing your question
- Use keywords from the topic you're searching for
- Use interactive mode to refine your query

## 💡 Tips

1. **Be specific with keywords**: "Perlmutter outage December" is better than "what happened"
2. **Interactive mode is great for exploring**: Start a session and ask multiple questions
3. **Results from both sources**: You'll see Google Docs results AND Slack messages
4. **No configuration needed**: Slack is pre-configured for you!

## 📖 Advanced Usage

### Search specific time periods
```bash
nersc-ask "What incidents in December?"
```

The system automatically:
- Searches Google Docs for December mentions
- Searches Slack for messages from December (last 7 days by default)

### Get different types of information
```bash
# Technical issues
nersc-ask "What problems with login nodes?"

# Events and announcements
nersc-ask "What seminars this week?"

# Status updates
nersc-ask "Current system status?"
```

## 🔒 Privacy & Security

- **Google authentication**: Uses your own Google credentials
- **Slack access**: Uses a shared bot (read-only access to public channels)
- **AI mode (optional)**: Sends content to Anthropic API only if you set ANTHROPIC_API_KEY

## 📞 Support

- **Documentation**: `/global/common/software/nersc/google-docs-qa/README.md`
- **Questions**: support@nersc.gov
- **More examples**: See the docs folder

---

**Quick Start:** Just run:
```bash
module load python/3.11
nersc-ask "Your question here"
```

That's it! 🎊
