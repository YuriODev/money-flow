# Money Flow - Troubleshooting Guide

> Solutions for common issues and error messages

---

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [Payment Management Issues](#payment-management-issues)
3. [AI Assistant Issues](#ai-assistant-issues)
4. [Telegram Issues](#telegram-issues)
5. [Import/Export Issues](#importexport-issues)
6. [Performance Issues](#performance-issues)
7. [Error Messages](#error-messages)
8. [Browser Issues](#browser-issues)

---

## Authentication Issues

### "Invalid credentials" when logging in

**Symptoms**: Can't log in despite using correct email/password

**Solutions**:
1. Check for typos in email and password
2. Ensure Caps Lock is off
3. Try resetting your password via "Forgot Password"
4. Clear browser cookies and try again
5. Check if your account has been locked (5 failed attempts)

### Session keeps expiring

**Symptoms**: Getting logged out frequently

**Solutions**:
1. Ensure browser cookies are enabled
2. Check your device clock is accurate (JWT validation depends on time)
3. Disable browser extensions that clear cookies
4. Try using a different browser
5. Check if you're using private/incognito mode

### "Account locked" message

**Symptoms**: Cannot log in, account locked

**Solutions**:
1. Wait 15 minutes for automatic unlock
2. Contact support if the issue persists
3. Reset your password to immediately unlock

### Registration fails

**Symptoms**: Can't create new account

**Check**:
- Email format is valid
- Password meets requirements:
  - At least 8 characters
  - One uppercase letter
  - One lowercase letter
  - One number
  - One special character (!@#$%^&*)
- Email isn't already registered

---

## Payment Management Issues

### Payment not appearing in list

**Symptoms**: Added payment but can't see it

**Solutions**:
1. Refresh the page
2. Check filters - you might be filtering by type/status
3. Clear search box if you were searching
4. Check if the payment was created in a different currency view

### Can't edit a payment

**Symptoms**: Edit button doesn't work or changes don't save

**Solutions**:
1. Check your internet connection
2. Refresh the page and try again
3. Check browser console for errors (F12 → Console)
4. Try a different browser
5. Clear browser cache

### Payment totals seem incorrect

**Symptoms**: Monthly/yearly totals don't match expectations

**Check**:
1. All relevant payments are marked "Active"
2. Frequencies are set correctly
3. Multi-currency payments are being converted
4. No duplicate payments

**Calculate manually**:
```
Monthly Total = Sum of:
- Monthly payments × 1
- Weekly payments × 4.33
- Quarterly payments ÷ 3
- Yearly payments ÷ 12
```

### Next payment date is wrong

**Symptoms**: Date shows in the past or wrong day

**Solutions**:
1. Edit the payment and manually set the correct date
2. Check if the frequency is correct
3. For monthly payments on day 31, it may roll to 30/28 for shorter months

### Duplicate payments

**Symptoms**: Same payment appears twice

**Solutions**:
1. Delete the duplicate
2. Check import history - may have imported twice
3. AI may have created a new one instead of updating existing

---

## AI Assistant Issues

### AI not responding

**Symptoms**: No response after sending message

**Solutions**:
1. Check internet connection
2. Refresh the page
3. Check if AI service is available (status indicator)
4. Try a simpler command
5. Clear conversation and start fresh

### AI misunderstands commands

**Symptoms**: AI creates wrong payment or doesn't understand

**Solutions**:
1. Be more specific:
   - Bad: "Add Netflix"
   - Good: "Add Netflix subscription £15.99 monthly"
2. Specify currency explicitly: "£15.99" not "15.99"
3. Use clear payment types: "as a subscription", "as housing"
4. Check for typos in your message

### AI creates wrong payment type

**Symptoms**: Payment categorized incorrectly

**Solutions**:
1. Specify type in command: "Add X as a subscription"
2. Edit the payment afterward to change type
3. Common auto-detections:
   - "rent" → Housing
   - "electric" → Utility
   - "insurance" → Insurance

### AI can't find a payment to update

**Symptoms**: "I couldn't find a payment called X"

**Solutions**:
1. Check the exact payment name
2. Use part of the name: "Update Netflix" vs "Update Netflix Premium"
3. List payments first to see exact names
4. Edit manually via the UI

### Conversation context lost

**Symptoms**: AI doesn't remember previous messages

**Solutions**:
1. Refresh may clear context - start fresh
2. Be explicit: "Update Netflix to £18.99" vs "Change it to £18.99"
3. Long conversations may lose older context

---

## Telegram Issues

### Verification code not working

**Symptoms**: Bot doesn't recognize code

**Solutions**:
1. Send only the code (e.g., "A3F2B1"), no extra text
2. Codes expire after 10 minutes - generate a new one
3. Ensure you're messaging the correct bot
4. Check for spaces before/after the code

### Not receiving notifications

**Symptoms**: No Telegram reminders

**Check**:
1. Settings → Notifications → Telegram Status shows "Connected"
2. "Reminder Enabled" is turned on
3. "Days Before" is set (default: 3)
4. Payment is marked as Active
5. Next payment date is within reminder window

**Telegram-side checks**:
1. Ensure you haven't blocked the bot
2. Check Telegram notification settings
3. Try sending /status to the bot

### Bot shows "Not linked"

**Symptoms**: /status says account not linked

**Solutions**:
1. Go to Settings → Notifications → Connect Telegram
2. Follow the linking process again
3. If previously linked, click "Disconnect" then reconnect

### Telegram shows wrong payment info

**Symptoms**: Reminder has incorrect details

**Solutions**:
1. Update the payment in Money Flow
2. Changes should reflect in next notification
3. Wait for next scheduled reminder

### Test notification not received

**Symptoms**: "Send Test" clicked but no message

**Solutions**:
1. Check Telegram is connected (green status)
2. Check Telegram app for the message
3. Ensure the bot isn't muted
4. Try reconnecting Telegram

---

## Import/Export Issues

### Export fails

**Symptoms**: Can't download export file

**Solutions**:
1. Check browser allows downloads
2. Try a different format (JSON vs CSV)
3. Check for popup blockers
4. Try a different browser

### Import fails

**Symptoms**: "Import failed" error

**Common causes**:
1. **Wrong format**: Ensure JSON/CSV matches expected structure
2. **Invalid data**: Check for missing required fields
3. **Large file**: Break into smaller chunks
4. **Encoding issues**: Save file as UTF-8

### Import creates duplicates

**Symptoms**: Same payments appear twice after import

**Solutions**:
1. Export before importing to have a backup
2. Delete duplicates manually
3. Use unique payment names
4. Check if you imported the same file twice

### CSV format issues

**Expected CSV columns**:
```csv
name,amount,currency,frequency,payment_type,next_payment_date,card_name,is_active
```

**Common issues**:
- Missing headers
- Wrong column order
- Invalid date format (use YYYY-MM-DD)
- Invalid payment_type (use: subscription, housing, utility, etc.)

---

## Performance Issues

### App is slow to load

**Solutions**:
1. Clear browser cache
2. Check internet connection speed
3. Disable browser extensions
4. Try incognito/private mode
5. Check if issue persists in different browser

### List takes long to load

**Symptoms**: Payment list loads slowly

**Solutions**:
1. Reduce number of payments displayed (pagination)
2. Use filters to narrow results
3. Clear browser cache
4. Check network tab for slow requests

### AI responses are slow

**Symptoms**: Long wait for AI responses

**Possible causes**:
1. AI service under heavy load
2. Complex query processing
3. Network latency

**Solutions**:
1. Wait a moment and retry
2. Use simpler queries
3. Check your internet connection

---

## Error Messages

### 401 Unauthorized

**Meaning**: Session expired or invalid token

**Solution**: Log out and log back in

### 403 Forbidden

**Meaning**: No permission to access resource

**Solution**: Ensure you're accessing your own data. Log out and back in.

### 404 Not Found

**Meaning**: Resource doesn't exist

**Solution**: Check if payment/card was deleted. Refresh the page.

### 429 Too Many Requests

**Meaning**: Rate limit exceeded

**Solution**: Wait 1 minute before trying again. Avoid rapid repeated requests.

### 500 Internal Server Error

**Meaning**: Server-side error

**Solution**: Wait a moment and retry. If persists, report the issue.

### 503 Service Unavailable

**Meaning**: Service temporarily unavailable

**Solution**: Wait and retry. Usually resolves within minutes.

### "Network Error"

**Meaning**: Can't connect to server

**Check**:
1. Internet connection
2. VPN/proxy settings
3. Firewall blocking requests
4. Server status

---

## Browser Issues

### Recommended Browsers

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Known Issues by Browser

**Safari**:
- Private mode may cause session issues
- Enable "Prevent cross-site tracking" exceptions

**Firefox**:
- Enhanced Tracking Protection may block some features
- Try standard protection mode

**Brave**:
- Shields may block API requests
- Add site to allowed list

### Clearing Cache

**Chrome**:
1. Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac)
2. Select "Cached images and files"
3. Click "Clear data"

**Firefox**:
1. Ctrl+Shift+Delete
2. Select "Cache"
3. Click "Clear Now"

**Safari**:
1. Safari → Preferences → Privacy
2. Click "Manage Website Data"
3. Remove site data

### Console Errors

To view errors:
1. Press F12 (or Cmd+Option+I on Mac)
2. Go to "Console" tab
3. Look for red error messages

Common console errors:
- **CORS errors**: Server configuration issue, contact support
- **NetworkError**: Connection issue, check internet
- **SyntaxError**: Report as a bug

---

## Still Having Issues?

If you've tried the solutions above and still have problems:

1. **Check the FAQ**: [FAQ.md](FAQ.md)
2. **Review the User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
3. **Report a Bug**: Include:
   - What you were doing
   - What you expected
   - What happened instead
   - Browser and OS version
   - Any error messages (screenshot console)

---

*Last Updated: December 2025*
*Version: 1.0.0*
