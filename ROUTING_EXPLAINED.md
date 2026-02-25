# How Smart Routing Works - Complete Guide

## 🧠 The Algorithm

The system uses **keyword-based scoring** to automatically decide which sources to search.

### Step-by-Step Process

When you ask: **"What outages happened in December?"**

**Step 1: Extract Question Keywords**
- Convert to lowercase: `"what outages happened in december?"`

**Step 2: Score Each Source**
For each Google Doc and Slack channel, count how many of its keywords appear in the question:

**Google Docs:**
```
NERSC Downtimes (Sept-Dec):
  Keywords: downtime, outage, incident, perlmutter, maintenance, unplanned, planned, login nodes, batch system
  Matches: "outage" ✓
  Score: 1
```

**Slack Channels:**
```
#fire:
  Keywords: incident, outage, downtime, emergency, critical, fire, issue
  Matches: "outage" ✓
  Score: 1

#general:
  Keywords: general, announcement, meeting, event
  Matches: none
  Score: 0

#hpcpoc:
  Keywords: perlmutter, hpc, compute, performance
  Matches: none
  Score: 0
```

**Step 3: Select Top Scorers**
- Google Docs: Top 2 (max_per_source = 2)
  - ✓ NERSC Downtimes (Score: 1)
- Slack: Top 2 (max_per_source = 2)
  - ✓ #fire (Score: 1)

**Step 4: Search Selected Sources**
- Query Google Docs: NERSC Downtimes
- Query Slack: #fire

---

## 📊 Real Examples

### Example 1: "What outages happened in December?"

**Selected Sources:**
- 📄 Google Docs: NERSC Downtimes (matched: `outage`)
- 💬 Slack: #fire (matched: `outage`)

**Why:** Both sources have "outage" in their keywords

---

### Example 2: "What events are happening this week?"

**Selected Sources:**
- 💬 Slack: #general (matched: `event`)

**Why:** Only #general has "event" in its keywords

---

### Example 3: "Perlmutter performance issues with login nodes"

**Selected Sources:**
- 📄 Google Docs: NERSC Downtimes (matched: `perlmutter`, `login nodes`) - Score: 2
- 💬 Slack: #hpcpoc (matched: `perlmutter`, `performance`) - Score: 2
- 💬 Slack: #fire (matched: `issue`) - Score: 1

**Why:** Multiple keyword matches = higher scores = selected

---

## ⚙️ Configuration

The routing behavior is controlled by `documents_config.yaml`:

### Adding Keywords to Sources

**For Google Docs:**
```yaml
google_docs:
  - id: "doc_id_here"
    name: "Document Name"
    keywords:
      - keyword1
      - keyword2
      - "multi word keyword"
```

**For Slack Channels:**
```yaml
slack_channels:
  - name: "channel-name"
    keywords:
      - keyword1
      - keyword2
```

### Search Strategy Options

```yaml
search_strategy:
  # Which sources to search
  sources:
    - google_docs
    - slack

  # Selection mode
  mode: "smart"  # Options:
                 #   "smart" - keyword matching (recommended)
                 #   "all" - search all sources
                 #   "first" - search only first source

  # Maximum sources per type
  max_per_source: 2  # Max Google Docs + Max Slack channels

  # Slack settings
  slack_days_back: 7
  slack_max_messages: 10
```

---

## 🎯 How to Optimize Keywords

### Good Keywords
✅ **Specific terms** - `perlmutter`, `login nodes`, `outage`
✅ **Common phrases** - `incident`, `maintenance`, `event`
✅ **Technical terms** - `batch system`, `performance`, `GPU`

### Poor Keywords
❌ **Too generic** - `the`, `a`, `is`
❌ **Too rare** - words that never appear in questions
❌ **Duplicates** - same word in multiple sources

### Example: Adding a New Document

```yaml
google_docs:
  - id: "new_doc_id"
    name: "GPU Troubleshooting Guide"
    category: "documentation"
    keywords:
      - GPU
      - graphics
      - cuda
      - troubleshoot
      - nvidia
      - A100
    description: "GPU-related issues and solutions"
```

Now queries like **"GPU not working"** will automatically find this document!

---

## 🔍 Testing Your Keywords

Use the routing explainer:

```bash
python explain_routing.py "Your test question"
```

This shows:
- Which sources match
- What keywords matched
- Final scores
- Selected sources

**Example:**
```bash
$ python explain_routing.py "GPU issues on Perlmutter"

📄 GOOGLE DOCS SCORING:
  GPU Troubleshooting Guide                Score: 1
    Matched keywords: GPU
  NERSC Downtimes (Sept-Dec)               Score: 1
    Matched keywords: perlmutter

💬 SLACK CHANNELS SCORING:
  #hpcpoc                                   Score: 1
    Matched keywords: perlmutter
  #fire                                     Score: 1
    Matched keywords: issue

Selected: 2 Google Docs, 2 Slack channels
```

---

## 🎨 Advanced Patterns

### Pattern 1: Category-Based Routing

Group sources by category for easier management:

```yaml
google_docs:
  - id: "..."
    category: "incidents"
    keywords: [outage, incident, downtime]

  - id: "..."
    category: "documentation"
    keywords: [guide, howto, tutorial]

  - id: "..."
    category: "meetings"
    keywords: [meeting, notes, agenda]
```

### Pattern 2: Time-Sensitive Sources

For recent vs. historical information:

```yaml
# Recent incidents (last 3 months)
- id: "recent_doc"
  name: "Recent Incidents"
  keywords: [recent, current, latest, now, today]

# Historical incidents (older)
- id: "archive_doc"
  name: "2024 Incident Archive"
  keywords: [archive, historical, 2024, past]
```

### Pattern 3: System-Specific Sources

Different documents for different systems:

```yaml
google_docs:
  - id: "perlmutter_doc"
    keywords: [perlmutter, PM, GPU, A100]

  - id: "cori_doc"
    keywords: [cori, KNL, haswell]

  - id: "archive_doc"
    keywords: [archive, HPSS, storage, tape]
```

---

## 📈 Default Behavior

If no keywords match, the system uses the `default_category`:

```yaml
search_strategy:
  default_category: "incidents"
```

This means questions with no matches will search sources in the "incidents" category.

---

## 💡 Pro Tips

1. **Use user language**: Include terms users actually say
   - ✅ `login nodes` not just `authentication`
   - ✅ `down` not just `unavailable`

2. **Include synonyms**: Same concept, different words
   - `outage`, `downtime`, `offline`, `unavailable`

3. **Test frequently**: Run `explain_routing.py` with common questions

4. **Monitor usage**: See what users ask and add those keywords

5. **Start broad**: Better to search too much than miss relevant info

---

## 🔧 Tuning Parameters

### Increase Search Coverage
```yaml
max_per_source: 3  # Search more sources (default: 2)
```

### Search Everything
```yaml
mode: "all"  # Ignore keywords, search all sources
```

### Search Only Best Match
```yaml
max_per_source: 1  # Only search top-scoring source
```

---

## 🎯 Quick Reference

| Question Contains | Searches |
|-------------------|----------|
| `outage`, `incident`, `downtime` | Google Docs (Downtimes) + Slack (#fire) |
| `event`, `announcement`, `meeting` | Slack (#general) |
| `perlmutter`, `performance`, `hpc` | Google Docs (Downtimes) + Slack (#hpcpoc) |
| `login nodes`, `batch system` | Google Docs (Downtimes) |

---

## 📞 Debugging

**Not finding what you need?**

1. Check keywords:
   ```bash
   python explain_routing.py "your question"
   ```

2. Add missing keywords to `documents_config.yaml`

3. Verify source is configured correctly

4. Test again!

---

**Summary:** The system automatically picks the right sources based on keyword matching. You can customize which sources get searched by editing the keywords in `documents_config.yaml`.
