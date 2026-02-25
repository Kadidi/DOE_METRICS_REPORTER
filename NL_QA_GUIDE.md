# Natural Language Q&A for Google Docs - User Guide

## 🎯 What This Does

Ask questions about your Google Docs in natural language and get intelligent answers!

## 🚀 Quick Start

### Option 1: Simple Keyword Search (No API Key Required)

```bash
module load python/3.11
python ask_document.py <DOCUMENT_ID> "Your question here"
```

**Example:**
```bash
python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8 "What were the unplanned outages?"
```

### Option 2: AI-Powered Answers (Recommended - Requires Claude API Key)

1. **Get an Anthropic API key:**
   - Visit: https://console.anthropic.com/
   - Sign up and get your API key

2. **Set your API key:**
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

3. **Ask questions:**
   ```bash
   python ask_document.py <DOCUMENT_ID> "Your question here"
   ```

## 📖 Usage Examples

### Single Question Mode

```bash
# Ask about unplanned outages
python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8 \
  "What were the unplanned outages in December?"

# Ask about maintenance windows
python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8 \
  "How many planned maintenance windows were there?"

# Ask about specific issues
python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8 \
  "What problems occurred with login nodes?"

# Ask for summaries
python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8 \
  "Summarize all the issues in October"
```

### Interactive Mode

```bash
# Start interactive Q&A session
python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8
```

Then type questions interactively:
```
❓ Your question: What happened on December 15?
💡 Answer: On December 15, there was an unplanned outage from 03:00 to 08:41 where login to login nodes didn't work.

❓ Your question: How long was the longest outage?
💡 Answer: ...

❓ Your question: quit
```

## 🔧 Advanced Usage

### From Python Code

```python
from ask_document import get_document_content, ask_document_with_claude
from test_google_docs import get_credentials

# Get document
creds = get_credentials()
title, content = get_document_content(creds, "DOCUMENT_ID")

# Ask questions
answer = ask_document_with_claude(
    document_title=title,
    document_content=content,
    question="What were the main issues?",
    api_key="your-api-key"  # Or set ANTHROPIC_API_KEY env var
)

print(answer)
```

### Batch Processing Multiple Questions

```bash
# Create a file with questions (one per line)
cat > questions.txt <<EOF
What were the unplanned outages?
How many planned maintenance windows?
What issues occurred with login nodes?
Summarize the December incidents
EOF

# Process each question
while read question; do
  echo "Q: $question"
  python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8 "$question"
  echo "---"
done < questions.txt
```

## 🆚 Comparison: Simple vs AI-Powered

| Feature | Simple Search | AI-Powered (Claude) |
|---------|--------------|---------------------|
| Setup | None | Requires API key |
| Speed | Fast | ~2-3 seconds |
| Cost | Free | ~$0.001 per query |
| Accuracy | Keyword matching | Deep understanding |
| Summaries | No | Yes |
| Context | Limited | Full document context |
| Complex questions | No | Yes |

### Example Question Comparison

**Question:** "How many login node issues happened in December?"

**Simple Search:**
```
Found 2 lines with "login" and "December":
- 12/15 03:00 to 08:41 unplanned (login to login nodes didn't work)
- 12/18 02:25 to 09:25 unplanned (login nodes didn't work)
```

**AI-Powered:**
```
There were 2 login node issues in December:
1. December 15: Unplanned outage from 03:00 to 08:41 where login to login nodes didn't work
2. December 18: Unplanned outage from 02:25 to 09:25 where login nodes didn't work

Both were unplanned incidents affecting user access to the system.
```

## 💡 Best Practices

1. **For simple lookups**: Use keyword search (no API key needed)
2. **For analysis**: Use AI-powered mode for summaries, counts, comparisons
3. **Save API costs**: Cache frequently asked questions
4. **Be specific**: More specific questions get better answers
5. **Interactive mode**: Great for exploring documents

## 🔒 Security Notes

- API key is sent to Anthropic servers
- Document content is sent to Claude API for processing
- For sensitive documents, use simple keyword search instead
- Token file (`token.json`) contains OAuth credentials - keep secure

## 📊 Example Queries by Type

### Timeline Questions
- "What happened on October 7?"
- "When was the last maintenance window?"
- "How long did the December 15 outage last?"

### Counting Questions
- "How many unplanned outages were there?"
- "Count the maintenance windows in November"
- "How many times did login nodes fail?"

### Analysis Questions
- "What was the most common type of failure?"
- "Compare planned vs unplanned downtime"
- "Which month had the most incidents?"

### Summary Questions
- "Summarize all incidents in December"
- "Give me an overview of batch system issues"
- "What are the main findings from this document?"

## 🛠 Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
# Add to ~/.bashrc to persist
```

### "Document not found"
Make sure you've authenticated with Google first:
```bash
python test_google_docs.py
```

### "API rate limit"
Wait a few minutes or switch to simple keyword search mode.

## 🎓 Next Steps

1. Try both modes with your document
2. Set up your ANTHROPIC_API_KEY for better results
3. Integrate into your DOE_METRICS_REPORTER workflow
4. Create saved queries for common questions
5. Build automated report generation

---

**Your test document ID:** `1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8`

**Quick test command:**
```bash
python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8 "What incidents happened?"
```
