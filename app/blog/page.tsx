import { Metadata } from 'next'
import Link from 'next/link'
import { getAllPosts, getFeaturedPosts } from '@/lib/blog-posts'

export const metadata: Metadata = {
  title: 'Blog - QuickSync',
  description: 'Learn how to convert bank statements to CSV/QBO, streamline QuickBooks workflows, and save time on bookkeeping tasks.',
  keywords: ['bank statement converter', 'PDF to CSV', 'QuickBooks tips', 'bookkeeping guides', 'accounting automation'],
}

export default function BlogPage() {
  const allPosts = getAllPosts()
  const featuredPosts = getFeaturedPosts()

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-16">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Blog & Guides
          </h1>
          <p className="text-lg sm:text-xl text-gray-600 max-w-3xl">
            Learn how to streamline your bookkeeping workflow, convert bank statements efficiently, and get the most out of QuickBooks.
          </p>
        </div>
      </div>

      {/* Featured Posts */}
      {featuredPosts.length > 0 && (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Featured</h2>
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {featuredPosts.map((post) => (
              <Link
                key={post.slug}
                href={`/blog/${post.slug}`}
                className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow overflow-hidden"
              >
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2 hover:text-blue-600">
                    {post.title}
                  </h3>
                  <p className="text-gray-600 mb-4 line-clamp-3">{post.description}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>{new Date(post.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
                    <span className="text-blue-600 hover:text-blue-700 font-medium">
                      Read more →
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* All Posts */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">All Posts</h2>
        <div className="space-y-6">
          {allPosts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6"
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2 hover:text-blue-600">
                    {post.title}
                  </h3>
                  <p className="text-gray-600 mb-3">{post.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {post.keywords.slice(0, 3).map((keyword) => (
                      <span
                        key={keyword}
                        className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-sm text-gray-500 whitespace-nowrap">
                  {new Date(post.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-white border-t">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="bg-blue-50 rounded-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Ready to Convert Your Bank Statements?
            </h2>
            <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
              Try QuickSync free - convert your first bank statement PDF to QuickBooks-ready CSV or QBO files in minutes.
            </p>
            <Link
              href="/"
              className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </div>
    </main>
  )
}

