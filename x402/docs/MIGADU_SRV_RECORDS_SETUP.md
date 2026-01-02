# Migadu SRV Records Setup Guide

**Domain:** quicksync.app  
**Purpose:** Email client autodiscovery (optional but recommended)

---

## ✅ What You Need to Add

These 4 SRV records help email clients (Outlook, Apple Mail, etc.) automatically detect email server settings. They're **optional** but recommended.

---

## 📋 SRV Record Format

SRV records have this format:
```
_Service._Protocol.Name TTL Priority Weight Port Target
```

For DNS providers, you'll typically enter:
- **Service:** `_autodiscover`, `_submissions`, `_imaps`, `_pop3s`
- **Protocol:** `_tcp`
- **Name:** `quicksync.app` (or leave blank/use @ if that's your root domain)
- **Priority:** `0`
- **Weight:** `1`
- **Port:** `443`, `465`, `993`, or `995`
- **Target:** The server hostname (with trailing dot in some systems)

---

## 🔧 Records to Add

### 1. Autodiscover (Outlook)
**Service Name:** `_autodiscover._tcp`  
**Priority:** `0`  
**Weight:** `1`  
**Port:** `443`  
**Target:** `autodiscover.migadu.com.` (note the trailing dot)

**Full format:** `0 1 443 autodiscover.migadu.com.`

---

### 2. SMTP Submissions
**Service Name:** `_submissions._tcp`  
**Priority:** `0`  
**Weight:** `1`  
**Port:** `465`  
**Target:** `smtp.migadu.com.` (note the trailing dot)

**Full format:** `0 1 465 smtp.migadu.com.`

---

### 3. IMAPS (Incoming Mail)
**Service Name:** `_imaps._tcp`  
**Priority:** `0`  
**Weight:** `1`  
**Port:** `993`  
**Target:** `imap.migadu.com.` (note the trailing dot)

**Full format:** `0 1 993 imap.migadu.com.`

---

### 4. POP3S (Incoming Mail - Optional)
**Service Name:** `_pop3s._tcp`  
**Priority:** `0`  
**Weight:** `1`  
**Port:** `995`  
**Target:** `pop.migadu.com.` (note the trailing dot)

**Full format:** `0 1 995 pop.migadu.com.`

---

## 🌐 DNS Provider Specific Instructions

### **Cloudflare DNS**

1. Go to Cloudflare Dashboard → DNS → Records
2. Click "Add record"
3. Select Type: **SRV**
4. Fill in for each record:

**For Autodiscover:**
- **Service:** `_autodiscover._tcp`
- **Name:** `quicksync.app` (or leave blank if root domain)
- **Priority:** `0`
- **Weight:** `1`
- **Port:** `443`
- **Target:** `autodiscover.migadu.com` (no trailing dot in Cloudflare)

**For Submissions:**
- **Service:** `_submissions._tcp`
- **Name:** `quicksync.app`
- **Priority:** `0`
- **Weight:** `1`
- **Port:** `465`
- **Target:** `smtp.migadu.com`

**For IMAPS:**
- **Service:** `_imaps._tcp`
- **Name:** `quicksync.app`
- **Priority:** `0`
- **Weight:** `1`
- **Port:** `993`
- **Target:** `imap.migadu.com`

**For POP3S:**
- **Service:** `_pop3s._tcp`
- **Name:** `quicksync.app`
- **Priority:** `0`
- **Weight:** `1`
- **Port:** `995`
- **Target:** `pop.migadu.com`

---

### **Vercel DNS**

If you're using Vercel DNS:
1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Click on `quicksync.app`
3. Add DNS records
4. Vercel may have limited SRV record support - check if SRV is available

**Note:** If Vercel doesn't support SRV records, you can:
- Skip these (they're optional)
- Use Cloudflare DNS instead (recommended)

---

### **Namecheap**

1. Go to Namecheap Dashboard → Domain List → Manage
2. Go to "Advanced DNS" tab
3. Click "Add New Record"
4. Select Type: **SRV Record**

**Format:**
- **Host:** `_autodiscover._tcp` (for first record)
- **Value:** `0 1 443 autodiscover.migadu.com.`
- **TTL:** Automatic (or 3600)

Repeat for each of the 4 records.

---

### **GoDaddy**

1. Go to GoDaddy DNS Management
2. Click "Add"
3. Select Type: **SRV**

**Fill in:**
- **Service:** `_autodiscover`
- **Protocol:** `_tcp`
- **Name:** `quicksync.app` or `@`
- **Priority:** `0`
- **Weight:** `1`
- **Port:** `443`
- **Target:** `autodiscover.migadu.com.`

Repeat for each record.

---

### **Generic DNS Provider**

If your DNS provider has a generic SRV record option:

**Record Format:**
```
_Service._Protocol.Name  TTL  IN  SRV  Priority Weight Port Target
```

**Examples:**
```
_autodiscover._tcp.quicksync.app.  3600  IN  SRV  0 1 443 autodiscover.migadu.com.
_submissions._tcp.quicksync.app.  3600  IN  SRV  0 1 465 smtp.migadu.com.
_imaps._tcp.quicksync.app.  3600  IN  SRV  0 1 993 imap.migadu.com.
_pop3s._tcp.quicksync.app.  3600  IN  SRV  0 1 995 pop.migadu.com.
```

---

## ⚠️ Common Issues

### Issue 1: "Service name format not recognized"
**Solution:** Make sure you include both `_service._protocol` (e.g., `_autodiscover._tcp`)

### Issue 2: "Target needs trailing dot"
**Solution:** Some DNS providers require trailing dot (`.`) on target hostname, others don't. Try both:
- With dot: `autodiscover.migadu.com.`
- Without dot: `autodiscover.migadu.com`

### Issue 3: "Name field"
**Solution:** 
- Some providers: Leave blank or use `@` for root domain
- Some providers: Enter full domain `quicksync.app`
- Some providers: The service name IS the name (combined)

### Issue 4: DNS Provider Doesn't Support SRV
**Solution:** 
- These records are **optional**
- Email will still work without them
- Email clients just won't auto-configure (users will need to enter settings manually)

---

## ✅ Quick Reference Table

| Service Name | Priority | Weight | Port | Target |
|--------------|----------|--------|------|--------|
| `_autodiscover._tcp` | 0 | 1 | 443 | `autodiscover.migadu.com` |
| `_submissions._tcp` | 0 | 1 | 465 | `smtp.migadu.com` |
| `_imaps._tcp` | 0 | 1 | 993 | `imap.migadu.com` |
| `_pop3s._tcp` | 0 | 1 | 995 | `pop.migadu.com` |

---

## 🧪 Testing

After adding records, wait 15-30 minutes for DNS propagation, then:

1. **Check in Migadu Dashboard:**
   - Go to DNS Configuration
   - Click "Check Configuration"
   - It will show which records are detected

2. **Test with DNS Tools:**
   ```bash
   # Check SRV records (replace with your DNS provider's tool)
   dig SRV _autodiscover._tcp.quicksync.app
   dig SRV _submissions._tcp.quicksync.app
   dig SRV _imaps._tcp.quicksync.app
   dig SRV _pop3s._tcp.quicksync.app
   ```

---

## 📝 Notes

- **These are optional** - Email will work without them
- **Main purpose:** Help email clients auto-configure
- **Required for QuickSync?** No - our app uses SMTP directly, not email clients
- **Can skip if:** Your DNS provider doesn't support SRV records easily
- **Recommended if:** You want users to be able to set up email clients easily

---

## 🚀 After Setup

Once all DNS records are added and verified:

1. Wait for DNS propagation (15 minutes to 24 hours)
2. Go back to Migadu Dashboard → DNS Configuration → "Check Configuration"
3. All records should show as detected
4. Create your `info@quicksync.app` mailbox
5. Get SMTP credentials and update your app's environment variables

---

**Which DNS provider are you using?** I can give you more specific instructions!

