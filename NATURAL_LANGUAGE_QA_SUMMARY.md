# Natural Language Q&A System - Complete Summary

## ✅ What's Been Built

You now have a complete natural language Q&A system for Google Docs with **two modes**:

### 1. Simple Keyword Search (No API Key)
- Fast, free, works immediately
- Good for simple lookups and keyword matching

### 2. AI-Powered (Claude API)
- Intelligent understanding of questions
- Can count, summarize, analyze, and compare
- Provides natural language responses
- Requires Anthropic API key

## 📁 Files Created

| File | Purpose |
|------|---------|
| `test_google_docs.py` | Core Google Docs API integration |
| `ask_document.py` | Natural language Q&A engine (main file) |
| `query_doc.py` | Direct document querying |
| `list_docs.py` | List your Google Docs |
| `quick_ask.sh` | Convenient wrapper script |
| `NL_QA_GUIDE.md` | Comprehensive user guide |
| `token.json` | Saved OAuth credentials |

## 🚀 Quick Start

### Easiest Way - Use the Wrapper Script

```bash
# Ask a question
./quick_ask.sh "What were the unplanned outages?"

# Interactive mode
./quick_ask.sh interactive
```

### Direct Python Usage

```bash
module load python/3.11

# Single question
python ask_document.py <DOC_ID> "Your question"

# Interactive Q&A
python ask_document.py <DOC_ID>
```

## 📝 Example Session

```bash
$ ./quick_ask.sh "What happened in December?"

📄 Fetching document...
✓ Loaded: NERSC Sept / Oct / Nov / Dec Downtimes
✓ Content: 697 characters

❓ Question: What happened in December?

💡 Answer:
--------------------------------------------------------------------------------
Based on 'NERSC Sept / Oct / Nov / Dec Downtimes', here are the relevant excerpts:

- 12/15 03:00 to 08:41 unplanned (login to login nodes didn't work)
- 12/17 06:00 to 17:40 planned (maintenance)
- 12/18 02:25 to 09:25 unplanned (login nodes didn't work)
--------------------------------------------------------------------------------
```

## 🎯 Usage Patterns

### For You (System Administrator)

```bash
# Quick checks
./quick_ask.sh "How many outages last month?"

# Detailed analysis (with Claude API)
export ANTHROPIC_API_KEY='your-key'
./quick_ask.sh "Compare planned vs unplanned downtime"

# Interactive exploration
./quick_ask.sh interactive
```

### For Other Users

Share `ask_document.py` and they can query any accessible Google Doc:

```bash
python ask_document.py <THEIR_DOC_ID> "Question about their document"
```

## 🔧 Setup for AI-Powered Mode

1. **Get API Key:**
   ```
   Visit: https://console.anthropic.com/
   Sign up and get your API key
   ```

2. **Set Environment Variable:**
   ```bash
   export ANTHROPIC_API_KEY='sk-ant-...'

   # Make it permanent (optional)
   echo "export ANTHROPIC_API_KEY='sk-ant-...'" >> ~/.bashrc
   ```

3. **Test It:**
   ```bash
   ./quick_ask.sh "Summarize all the incidents"
   ```

## 🌟 Key Features

### What You Can Ask

**✓ Timeline Questions**
- "What happened on October 7?"
- "When was the last maintenance?"

**✓ Counting Questions**
- "How many unplanned outages?"
- "Count the maintenance windows"

**✓ Search Questions**
- "What issues with login nodes?"
- "Find batch system problems"

**✓ Analysis (AI mode only)**
- "Summarize December incidents"
- "What was the most common failure?"
- "Compare September to December"

### Two Access Methods

**Command Line:**
```bash
./quick_ask.sh "Your question"
```

**Python API:**
```python
from ask_document import get_document_content, ask_document_with_claude
from test_google_docs import get_credentials

creds = get_credentials()
title, content = get_document_content(creds, doc_id)
answer = ask_document_with_claude(title, content, "Your question")
print(answer)
```

## 📊 Comparison: Simple vs AI

| Aspect | Simple Search | AI-Powered |
|--------|--------------|------------|
| **Cost** | Free | ~$0.001/query |
| **Speed** | Instant | 2-3 seconds |
| **Setup** | None | API key required |
| **Questions** | Simple keywords | Complex analysis |
| **Accuracy** | Exact matches | Contextual understanding |
| **Counting** | Manual | Automatic |
| **Summaries** | ❌ | ✅ |

## 🎓 Example Questions to Try

```bash
# Simple factual queries (works in both modes)
./quick_ask.sh "What happened on December 15?"
./quick_ask.sh "When was the planned maintenance?"

# Complex queries (better with AI)
./quick_ask.sh "How many times did login nodes fail?"
./quick_ask.sh "What was the longest outage?"
./quick_ask.sh "Summarize the September incidents"

# Analysis (AI only)
export ANTHROPIC_API_KEY='your-key'
./quick_ask.sh "What patterns do you see in the outages?"
./quick_ask.sh "Compare the frequency of planned vs unplanned events"
```

## 🔄 Integration Options

### Option 1: Standalone Tool
Use as-is for ad-hoc queries

### Option 2: Integrate with DOE_METRICS_REPORTER
```python
# In doe_metrics_client.py
from ask_document import get_document_content, ask_document_with_claude

# Add command:
# DOE_METRICS> ask <doc_id> <question>
```

### Option 3: Build a Web Interface
Create a simple web UI where users type questions

### Option 4: Scheduled Reports
```bash
# Cron job to generate daily summary
0 8 * * * ./quick_ask.sh "Summarize yesterday's incidents" > daily_report.txt
```

## 🛡️ Security Considerations

**✓ OAuth Token**
- `token.json` contains your Google credentials
- Keep it secure (already has 0600 permissions)

**✓ API Key**
- Don't commit to Git
- Use environment variable

**✓ Document Content**
- Simple mode: stays local
- AI mode: sent to Anthropic servers
- For sensitive docs: use simple mode only

## 📈 Next Steps

### Immediate (No API Key)
1. ✅ Test with simple keyword search
2. ✅ Try different questions
3. ✅ Share with team members

### Enhanced (With API Key)
1. Get Anthropic API key
2. Set `ANTHROPIC_API_KEY`
3. Try complex analytical questions
4. Build custom workflows

### Advanced
1. Integrate with DOE_METRICS_REPORTER
2. Add multiple document support
3. Create saved query templates
4. Build automated reporting

## 💡 Pro Tips

1. **Start simple**: Try keyword search first to understand what's in the document
2. **Be specific**: "What login node issues in December?" vs "What happened?"
3. **Use interactive mode**: Great for exploring unknown documents
4. **Cache answers**: For frequently asked questions, save the responses
5. **Combine modes**: Use simple search for speed, AI for analysis

## 📞 Support

**Test Document:** NERSC Sept/Oct/Nov/Dec Downtimes
**Document ID:** `1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8`

**Quick Test:**
```bash
./quick_ask.sh "What were the unplanned outages?"
```

**Full Guide:** See `NL_QA_GUIDE.md`

---

## ✨ Summary

You can now:
- ✅ Query Google Docs in natural language
- ✅ Get instant keyword-based answers (free)
- ✅ Get AI-powered intelligent answers (with API key)
- ✅ Use from command line or Python
- ✅ Interactive or single-query mode
- ✅ Share with other users

**Ready to use!** 🎉
