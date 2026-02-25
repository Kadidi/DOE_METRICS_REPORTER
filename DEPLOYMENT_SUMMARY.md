# Making Google Docs Q&A Available to All NERSC Users

## ✅ What You Have Now

All the code and documentation needed to deploy to all NERSC users!

## 🚀 Deployment Steps

### Option 1: Quick Automated Deployment (Recommended)

```bash
# Deploy to shared NERSC location
./deploy_to_nersc.sh /global/common/software/nersc/google-docs-qa
```

This will:
- ✅ Copy all necessary files
- ✅ Set correct permissions
- ✅ Create user-friendly wrapper scripts
- ✅ Generate documentation
- ✅ Create setup scripts for users

### Option 2: Manual Deployment

If you need more control:

1. **Contact NERSC Support** to request space:
   ```
   Email: support@nersc.gov
   Request: Directory for new user tool at /global/common/software/nersc/google-docs-qa
   Purpose: Natural language Q&A for Google Docs
   ```

2. **Copy files** once you have permissions:
   ```bash
   DEST="/global/common/software/nersc/google-docs-qa"
   mkdir -p $DEST
   cp *.py *.sh *.md $DEST/
   chmod -R 755 $DEST
   ```

3. **Create module file** (optional but recommended):
   ```bash
   # Location: /global/common/software/modulefiles/google-docs-qa/1.0.lua
   # See NERSC_DEPLOYMENT_GUIDE.md for template
   ```

---

## 📢 Announcing to Users

### Step 1: Update NERSC Documentation

Add page to https://docs.nersc.gov/:
- Copy content from `NL_QA_GUIDE.md`
- Add to "Tools" or "Utilities" section

### Step 2: Send Announcement Email

Use template from `USER_ANNOUNCEMENT.md`:
```bash
cat USER_ANNOUNCEMENT.md
```

### Step 3: Create Support Materials

Distribute:
- `QUICK_REFERENCE.md` - Print as handout
- Training video or slides (optional)
- FAQ document

---

## 👥 User Experience

### What Users Need to Do

**One-time setup (5 minutes):**

```bash
module load python/3.11
/global/common/software/nersc/google-docs-qa/setup_user.sh
```

**Daily usage:**

```bash
module load python/3.11
python /global/common/software/nersc/google-docs-qa/ask_document.py <DOC_ID> "question"
```

### What Gets Created for Each User

- `~/token.json` - Their personal Google OAuth credentials
- `~/.local/lib/python3.11/site-packages/` - Python dependencies (if not using shared env)

---

## 🎯 Deployment Checklist

### Before Deployment

- [ ] Test all scripts work on your account
- [ ] Verify Google Docs API access
- [ ] Check file permissions
- [ ] Review security implications
- [ ] Get NERSC admin approval
- [ ] Plan rollout strategy

### Deployment Day

- [ ] Run `./deploy_to_nersc.sh`
- [ ] Verify files are accessible by all users
- [ ] Test with a different user account
- [ ] Create module file (if using)
- [ ] Update NERSC documentation site

### After Deployment

- [ ] Send announcement email (use `USER_ANNOUNCEMENT.md`)
- [ ] Monitor support requests
- [ ] Gather user feedback
- [ ] Update documentation based on questions
- [ ] Plan training session (optional)

### Week 1-2

- [ ] Respond to user issues
- [ ] Update FAQ
- [ ] Consider improvements
- [ ] Track usage (optional)

---

## 📁 Files Ready for Deployment

### Core Scripts
- `test_google_docs.py` - Google Docs API authentication
- `ask_document.py` - Main Q&A engine
- `query_doc.py` - Direct document queries
- `list_docs.py` - List user's documents

### Deployment Tools
- `deploy_to_nersc.sh` - Automated deployment script ⭐
- `setup_user.sh` - User setup automation

### Documentation for Users
- `README.md` - Main documentation
- `NL_QA_GUIDE.md` - Comprehensive guide
- `QUICK_REFERENCE.md` - Quick reference card
- `NATURAL_LANGUAGE_QA_SUMMARY.md` - Complete feature list

### Documentation for Admins
- `NERSC_DEPLOYMENT_GUIDE.md` - Deployment options
- `USER_ANNOUNCEMENT.md` - Email template
- `DEPLOYMENT_SUMMARY.md` - This file

### Supporting Files
- `requirements.txt` - Python dependencies
- `quick_ask.sh` - Convenience wrapper

---

## 🔧 Recommended Deployment Path

### Phase 1: Preparation (This Week)

1. **Get approval** from NERSC management
   ```bash
   # Contact: support@nersc.gov or your manager
   ```

2. **Request shared directory**
   ```
   Location: /global/common/software/nersc/google-docs-qa
   Permissions: 755 (world-readable, you write)
   ```

3. **Test deployment script**
   ```bash
   # Test in your own directory first
   ./deploy_to_nersc.sh ~/test-deployment
   # Verify everything works
   ```

### Phase 2: Beta Testing (Week 1-2)

1. **Deploy to shared location**
   ```bash
   ./deploy_to_nersc.sh /global/common/software/nersc/google-docs-qa
   ```

2. **Invite 5-10 beta testers**
   - Pick users from different groups
   - Ask them to test and provide feedback

3. **Iterate based on feedback**
   - Fix issues
   - Update documentation
   - Improve user experience

### Phase 3: General Release (Week 3+)

1. **Send announcement email**
   - Use `USER_ANNOUNCEMENT.md` template
   - Send to all-users@nersc.gov

2. **Update NERSC documentation**
   - Add to https://docs.nersc.gov/
   - Link from relevant pages

3. **Provide support**
   - Monitor support tickets
   - Update FAQ
   - Consider office hours

### Phase 4: Long-term (Ongoing)

1. **Gather usage statistics** (optional)
2. **Plan enhancements** based on feedback
3. **Keep dependencies updated**
4. **Provide training sessions** (optional)

---

## 💡 Quick Start Options for Different Scenarios

### Scenario 1: You Have Admin Access

```bash
# Just run the deployment script
./deploy_to_nersc.sh /global/common/software/nersc/google-docs-qa

# Send announcement
cat USER_ANNOUNCEMENT.md | mail -s "New Tool Available" all-users@nersc.gov
```

### Scenario 2: Need Admin Approval

```bash
# 1. Email this to NERSC support:
cat << EOF
Hi NERSC Support,

I'd like to deploy a new tool for all users: Natural Language Q&A for Google Docs.

Request:
- Directory: /global/common/software/nersc/google-docs-qa
- Permissions: 755 (world-readable)
- Purpose: Allow users to query Google Docs with natural language
- Documentation: [attach NERSC_DEPLOYMENT_GUIDE.md]

The tool is ready to deploy. Can you create the directory or provide guidance?

Thanks!
EOF

# 2. Once approved, run deployment script
./deploy_to_nersc.sh /global/common/software/nersc/google-docs-qa
```

### Scenario 3: User-Initiated Installation

If shared deployment isn't possible, users can install individually:

```bash
# Users run this in their home directory:
git clone <your-repo-url> ~/google-docs-qa
cd ~/google-docs-qa
pip install --user -r requirements.txt
./test_google_docs.py  # Authenticate
./quick_ask.sh <doc_id> "question"
```

---

## 📊 Estimated Impact

### Time Savings for Users
- **Before**: Manual reading of Google Docs (10-30 min)
- **After**: Natural language query (< 1 min)
- **Savings**: ~95% time reduction for simple queries

### Expected Usage
- Incident response teams
- System administrators
- Documentation reviewers
- Project managers
- Anyone with Google Docs to analyze

---

## 🆘 Support Plan

### Common User Questions

**Q: Do I need to pay for anything?**
A: No! Basic keyword search is free. Optional AI mode requires your own API key (~$0.001/query).

**Q: Is my data secure?**
A: Yes! OAuth tokens stored in your home directory. Simple mode keeps data local. AI mode sends to Anthropic (optional).

**Q: Which documents can I access?**
A: Any Google Doc you have permission to view.

**Q: Does this work with Google Sheets/Slides?**
A: Currently Google Docs only. Sheets/Slides can be added.

### Support Channels

1. **Documentation** - Read the docs first
2. **Email** - support@nersc.gov
3. **Slack** - #google-docs-qa (if channel exists)
4. **Office Hours** - Weekly Q&A sessions (optional)

---

## ✅ Ready to Deploy!

You have everything needed to make this available to all NERSC users:

1. ✅ **Working code** - Tested and functional
2. ✅ **Deployment script** - One command to deploy
3. ✅ **User documentation** - Comprehensive guides
4. ✅ **Admin documentation** - Deployment guides
5. ✅ **Support materials** - Email templates, quick reference
6. ✅ **User setup automation** - Easy onboarding

**Next step:** Contact NERSC support or run the deployment script!

---

## 📞 Questions?

- **Technical**: Review `NERSC_DEPLOYMENT_GUIDE.md`
- **User docs**: See `NL_QA_GUIDE.md`
- **NERSC support**: support@nersc.gov
- **Quick test**: `./quick_ask.sh <doc_id> "test question"`

Good luck with the deployment! 🚀
