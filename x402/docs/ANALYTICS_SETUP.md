# Analytics Setup Guide

**Goal:** Track user behavior and conversion funnel

---

## Option 1: Plausible Analytics (Recommended - Privacy-Friendly)

### Why Plausible?

- ✅ Privacy-friendly (GDPR compliant, no cookies)
- ✅ Simple setup
- ✅ Lightweight
- ✅ Free for low traffic (< 10k pageviews/month)

### Setup Steps

1. **Sign up:** https://plausible.io/
2. **Add site:** `quicksync.app`
3. **Copy domain:** (shown in dashboard)
4. **Add to Vercel environment variables:**
   - Key: `NEXT_PUBLIC_PLAUSIBLE_DOMAIN`
   - Value: `quicksync.app` (your domain)
   - Environments: Production, Preview

5. **Code is already integrated!**

   The layout already checks for `NEXT_PUBLIC_PLAUSIBLE_DOMAIN` and loads Plausible if set.

   Check `app/layout.tsx` - it's already there! ✅

### Verify It Works

1. Deploy with the environment variable set
2. Visit https://quicksync.app
3. Check Plausible dashboard (may take a few minutes)
4. You should see pageviews

---

## Option 2: Google Analytics 4

### Setup Steps

1. **Create GA4 property:**
   - Go to: https://analytics.google.com/
   - Create property: "QuickSync"
   - Copy Measurement ID (format: `G-XXXXXXXXXX`)

2. **Add to Vercel environment variables:**
   - Key: `NEXT_PUBLIC_GA_MEASUREMENT_ID`
   - Value: `G-XXXXXXXXXX`
   - Environments: Production, Preview

3. **Add to `app/layout.tsx`:**

   Add this before `</head>`:

   ```tsx
   {process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID && (
     <>
       <Script
         src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID}`}
         strategy="afterInteractive"
       />
       <Script id="google-analytics" strategy="afterInteractive">
         {`
           window.dataLayer = window.dataLayer || [];
           function gtag(){dataLayer.push(arguments);}
           gtag('js', new Date());
           gtag('config', '${process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID}');
         `}
       </Script>
     </>
   )}
   ```

4. **Track events (optional):**

   Create `lib/analytics.ts`:

   ```typescript
   export function trackEvent(eventName: string, properties?: Record<string, any>) {
     if (typeof window !== 'undefined' && (window as any).gtag) {
       (window as any).gtag('event', eventName, properties)
     }
   }
   ```

   Use in components:

   ```typescript
   import { trackEvent } from '@/lib/analytics'
   
   trackEvent('file_uploaded', { fileName: file.name })
   ```

---

## Option 3: Vercel Analytics (Built-in)

### Setup Steps

1. **Install package:**
   ```bash
   npm install @vercel/analytics
   ```

2. **Add to `app/layout.tsx`:**

   ```tsx
   import { Analytics } from '@vercel/analytics/react'
   
   export default function RootLayout({ children }) {
     return (
       <html lang="en">
         <body>
           {children}
           <Analytics />
         </body>
       </html>
     )
   }
   ```

3. **That's it!**

   Analytics automatically enabled. View in Vercel Dashboard → Analytics tab.

---

## Recommended: Plausible (Already Integrated!)

**Quick Setup:**

1. Sign up at https://plausible.io/
2. Add site: `quicksync.app`
3. Add to Vercel:
   - `NEXT_PUBLIC_PLAUSIBLE_DOMAIN` = `quicksync.app`
4. Deploy
5. Done! ✅

**The code is already in `app/layout.tsx` - just needs the environment variable!**

---

## What to Track

### Key Metrics

1. **Pageviews**
   - Homepage
   - Job pages
   - Blog posts

2. **Conversion Funnel**
   - Upload started
   - File processed
   - Payment initiated
   - Payment completed
   - Download completed

3. **User Behavior**
   - Time on site
   - Bounce rate
   - Exit pages
   - Device/browser breakdown

### Custom Events (Optional)

Track important actions:

- File upload
- Payment initiation
- Payment completion
- Download
- Error events

---

## Next Steps

1. ✅ Choose analytics platform (Plausible recommended)
2. ✅ Set up account
3. ✅ Add environment variable to Vercel
4. ✅ Deploy
5. ✅ Verify tracking works
6. ✅ Monitor conversion funnel

---

## Privacy Notes

- **Plausible:** Privacy-friendly, GDPR compliant, no cookies
- **Google Analytics:** Requires cookie consent banner (GDPR)
- **Vercel Analytics:** Privacy-friendly, uses server-side tracking

For GDPR compliance, Plausible or Vercel Analytics are recommended.

