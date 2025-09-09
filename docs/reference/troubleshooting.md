# Troubleshooting Guide

## 🩺 Common Issues and Solutions

### OpenAI API Errors

#### Quota Exceeded

```
Error: "insufficient_quota" or "quota exceeded"
```

**Solution:**

- Check your OpenAI billing and usage at [https://platform.openai.com/account/usage](https://platform.openai.com/account/usage)
- Upgrade your OpenAI plan if needed
- Monitor API usage to avoid future interruptions
- System will automatically use fallback processing

#### Missing API Key

```
Error: "invalid_request_error" - API key issue
```

**Solution:**

```bash
# Set your API key in .env file
OPENAI_API_KEY=sk-your-key-here

# Or provide it temporarily
OPENAI_API_KEY=sk-your-key uv run python -m src.bank_statement_separator.main file.pdf
```

#### Rate Limiting

```
Error: 429 - "Too Many Requests"
```

**Solution:**

- System automatically retries and uses fallback processing
- For high-volume processing, consider implementing request throttling
- Check your API plan's rate limits

### Processing Issues

#### Boundary Detection Problems

**Symptoms:** Incorrect statement separation, fragments in output, or merged statements

**Common Causes:**

- Document fragments mixed with valid statements
- Weak statement headers in fallback mode
- Unusual document formatting

**Solutions:**

```bash
# Enable verbose logging to see boundary detection details
uv run python -m src.bank_statement_separator.main file.pdf --verbose --yes

# Check fragment detection logs
grep "fragment" /path/to/logs/statement_processing.log

# Use dry-run to preview boundary detection
uv run python -m src.bank_statement_separator.main file.pdf --dry-run --yes
```

**Fragment Detection (v0.1.0+):**
The system now automatically detects and filters document fragments:

- Fragments with confidence < 0.3 are automatically skipped
- Check logs for "Skipping fragment" messages
- Validation accounts for skipped fragment pages

#### No Statements Detected

**Symptoms:** Only 1 statement found, or incorrect boundaries

**Solutions:**

```bash
# Enable verbose logging to see details
uv run python -m src.bank_statement_separator.main file.pdf --verbose --yes

# Check if AI analysis is working (requires API key)
# Without API key, system uses enhanced fallback processing
```

#### File Access Denied

**Symptoms:** "File access denied by security configuration"

**Solutions:**

```bash
# Check your .env file settings
ALLOWED_INPUT_DIRS=./test/input,/path/to/your/files
ALLOWED_OUTPUT_DIRS=./test/output,/path/to/output

# Or remove restrictions (less secure)
# ALLOWED_INPUT_DIRS=
# ALLOWED_OUTPUT_DIRS=
```

#### Large File Processing

**Symptoms:** "File too large" or "Too many pages"

**Solutions:**

```bash
# Increase limits in .env file
MAX_FILE_SIZE_MB=200
MAX_TOTAL_PAGES=1000

# Or process in smaller chunks
```

### Performance Issues

#### Fast Processing (< 2 seconds)

**Likely Cause:** Using pattern-matching fallback instead of AI analysis

**Solutions:**

- Ensure `OPENAI_API_KEY` is properly set in `.env` file
- Verify your OpenAI account has available credits
- Check API connectivity

#### Slow Processing (> 10 seconds)

**Possible Causes:**

- API rate limiting or retries
- Large file processing
- Network connectivity issues

**Solutions:**

- Check logs for API retry attempts
- Consider processing smaller files
- Verify internet connectivity

### Debugging Steps

1. **Enable Verbose Logging:**

   ```bash
   uv run python -m src.bank_statement_separator.main file.pdf --verbose --yes
   ```

2. **Check Log Files:**

   ```bash
   cat ./logs/statement_processing.log
   tail -f ./logs/statement_processing.log  # Real-time monitoring
   ```

3. **Test Without API:**

   ```bash
   OPENAI_API_KEY="" uv run python -m src.bank_statement_separator.main file.pdf --dry-run --yes
   ```

4. **Validate PDF:**
   ```bash
   # Check if PDF is readable
   uv run python -c "
   from src.bank_statement_separator.utils.pdf_processor import PDFProcessor
   processor = PDFProcessor()
   print('PDF validation:', processor.validate_pdf('your-file.pdf'))
   "
   ```

### Fragment Detection Issues

#### Valid Statements Being Filtered (v0.1.0+)

**Symptoms:** Expected statements missing from output, "Skipping fragment" in logs

**Diagnosis:**

```bash
# Check what was filtered
grep "Skipping fragment" logs/statement_processing.log

# Review confidence scores
grep "confidence" logs/statement_processing.log
```

**Solutions:**

- **Lower threshold temporarily:** Set `FRAGMENT_CONFIDENCE_THRESHOLD=0.1` in `.env`
- **Check statement format:** Ensure statements have bank name, account number, and dates
- **Review patterns:** Statements should not start with single transactions

#### Fragments Still in Output

**Symptoms:** Incomplete pages or single transactions in separated files

**Solutions:**

- **Increase threshold:** Set `FRAGMENT_CONFIDENCE_THRESHOLD=0.5` in `.env`
- **Enable detection:** Ensure `ENABLE_FRAGMENT_DETECTION=true` in `.env`
- **Check logs:** Look for fragment detection warnings

### Getting Help

If you're still experiencing issues:

1. **Check the logs** - Most issues are explained in the log files
2. **Run with `--verbose`** - Get detailed processing information
3. **Try dry-run mode** - Test analysis without creating files
4. **Test fallback mode** - Run without API key to isolate issues
5. **Verify file format** - Ensure PDF is text-searchable, not scanned images
6. **Review fragment logs** - Check for fragment detection messages (v0.1.0+)

### Environment Checklist

- [ ] Python 3.11+ installed
- [ ] UV package manager installed
- [ ] Dependencies installed: `uv sync`
- [ ] `.env` file configured
- [ ] `OPENAI_API_KEY` set (optional, but recommended)
- [ ] Input/output directories exist and accessible
- [ ] PDF files are valid and text-searchable
- [ ] Sufficient disk space for output files

### Log File Locations

- **Main log:** `./logs/statement_processing.log`
- **Test logs:** `./test/logs/statement_processing.log`
- **Error logs:** Check console output and log files for ERROR level messages

### Support

For additional support, check:

- Project documentation in `README.md`
- Configuration examples in `.env.example`
- Test examples in `test/run_tests.sh`
