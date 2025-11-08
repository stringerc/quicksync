# SyncScript Local Development

This is a local development version of your Figma site, built with Next.js and TypeScript.

## Features

- ✅ **Landing Page**: Complete SyncScript landing page with hero section, features, and CTA
- ✅ **Dashboard Page**: Interactive dashboard with task management and AI insights
- ✅ **Responsive Design**: Mobile-first design that works on all devices
- ✅ **Interactive Elements**: All buttons and navigation work correctly
- ✅ **Modern UI**: Built with Tailwind CSS and shadcn/ui components

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Pages

- **Home Page** (`/`): Landing page with hero section, features, and call-to-action buttons
- **Dashboard** (`/dashboard`): Interactive dashboard with task management and AI insights

## Testing Navigation

1. **From Landing Page to Dashboard**:
   - Click "Get Started" button in navigation
   - Click "Start Free Trial" button in hero section
   - Click "Get Started Now" button in CTA section

2. **From Dashboard back to Home**:
   - Click "Back" button in dashboard navigation
   - Use browser back button

## Interactive Elements

All buttons and interactive elements are fully functional:

- ✅ Navigation menu (responsive)
- ✅ Call-to-action buttons
- ✅ Cookie consent banner
- ✅ Scroll-to-top button
- ✅ Mobile menu toggle
- ✅ Task management in dashboard
- ✅ AI insights cards
- ✅ Quick action buttons

## Deployment to Vercel

When you're ready to deploy:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add SyncScript local development version"
   git push origin main
   ```

2. **Deploy to Vercel**:
   - Connect your GitHub repository to Vercel
   - Vercel will automatically detect Next.js and deploy
   - Your site will be available at `https://your-project.vercel.app`

## Customization

- **Colors**: Update Tailwind colors in `tailwind.config.ts`
- **Content**: Modify text and content in `src/app/page.tsx` and `src/app/dashboard/page.tsx`
- **Components**: Add new components in `src/components/ui/`
- **Styling**: Update styles in `src/app/globals.css`

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Icons**: Lucide React
- **Deployment**: Vercel (ready)

## Notes

- The site replicates the functionality of your Figma site
- All interactive elements work as expected
- Responsive design matches the original
- Ready for production deployment