import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getPostBySlug, getAllPosts, getRelatedPosts } from '@/lib/blog-posts'

interface BlogPostPageProps {
  params: { slug: string }
}

export async function generateStaticParams() {
  const posts = getAllPosts()
  return posts.map((post) => ({
    slug: post.slug,
  }))
}

export async function generateMetadata({ params }: BlogPostPageProps): Promise<Metadata> {
  const post = getPostBySlug(params.slug)
  
  if (!post) {
    return {
      title: 'Post Not Found',
    }
  }

  return {
    title: post.title,
    description: post.description,
    keywords: post.keywords,
    openGraph: {
      title: post.title,
      description: post.description,
      type: 'article',
      publishedTime: post.date,
      authors: [post.author],
    },
  }
}

export default function BlogPostPage({ params }: BlogPostPageProps) {
  const post = getPostBySlug(params.slug)
  const relatedPosts = post ? getRelatedPosts(params.slug, 3) : []

  if (!post) {
    notFound()
  }

  // Simple markdown-like rendering (basic support)
  const renderContent = (content: string) => {
    // Split by headers and paragraphs
    const lines = content.split('\n')
    const elements: JSX.Element[] = []
    let currentParagraph: string[] = []
    let listItems: string[] = []
    let inList = false

    lines.forEach((line, index) => {
      const trimmed = line.trim()
      
      // Headers
      if (trimmed.startsWith('# ')) {
        if (currentParagraph.length > 0) {
          elements.push(<p key={`p-${index}`} className="mb-4 text-gray-700 leading-7">{currentParagraph.join(' ')}</p>)
          currentParagraph = []
        }
        if (inList) {
          elements.push(
            <ul key={`ul-${index}`} className="list-disc list-inside mb-4 space-y-2 text-gray-700">
              {listItems.map((item, i) => (
                <li key={i}>{item.replace(/^[-*]\s+/, '')}</li>
              ))}
            </ul>
          )
          listItems = []
          inList = false
        }
        elements.push(<h1 key={`h1-${index}`} className="text-3xl font-bold text-gray-900 mb-6 mt-8">{trimmed.substring(2)}</h1>)
        return
      }
      
      if (trimmed.startsWith('## ')) {
        if (currentParagraph.length > 0) {
          elements.push(<p key={`p-${index}`} className="mb-4 text-gray-700 leading-7">{currentParagraph.join(' ')}</p>)
          currentParagraph = []
        }
        if (inList) {
          elements.push(
            <ul key={`ul-${index}`} className="list-disc list-inside mb-4 space-y-2 text-gray-700">
              {listItems.map((item, i) => (
                <li key={i}>{item.replace(/^[-*]\s+/, '')}</li>
              ))}
            </ul>
          )
          listItems = []
          inList = false
        }
        elements.push(<h2 key={`h2-${index}`} className="text-2xl font-bold text-gray-900 mb-4 mt-8">{trimmed.substring(3)}</h2>)
        return
      }

      if (trimmed.startsWith('### ')) {
        if (currentParagraph.length > 0) {
          elements.push(<p key={`p-${index}`} className="mb-4 text-gray-700 leading-7">{currentParagraph.join(' ')}</p>)
          currentParagraph = []
        }
        if (inList) {
          elements.push(
            <ul key={`ul-${index}`} className="list-disc list-inside mb-4 space-y-2 text-gray-700">
              {listItems.map((item, i) => (
                <li key={i}>{item.replace(/^[-*]\s+/, '')}</li>
              ))}
            </ul>
          )
          listItems = []
          inList = false
        }
        elements.push(<h3 key={`h3-${index}`} className="text-xl font-semibold text-gray-900 mb-3 mt-6">{trimmed.substring(4)}</h3>)
        return
      }

      // List items
      if (trimmed.match(/^[-*]\s+/)) {
        if (currentParagraph.length > 0) {
          elements.push(<p key={`p-${index}`} className="mb-4 text-gray-700 leading-7">{currentParagraph.join(' ')}</p>)
          currentParagraph = []
        }
        inList = true
        listItems.push(trimmed)
        return
      }

      // Bold text (basic)
      if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
        const text = trimmed.slice(2, -2)
        if (currentParagraph.length === 0) {
          currentParagraph.push(`**${text}**`)
        } else {
          currentParagraph.push(`**${text}**`)
        }
        return
      }

      // Links (basic)
      if (trimmed.includes('[') && trimmed.includes('](')) {
        const match = trimmed.match(/\[([^\]]+)\]\(([^)]+)\)/)
        if (match) {
          const linkText = match[1]
          const linkUrl = match[2]
          if (currentParagraph.length === 0) {
            currentParagraph.push(`[${linkText}](${linkUrl})`)
          } else {
            currentParagraph.push(`[${linkText}](${linkUrl})`)
          }
          return
        }
      }

      // Empty line
      if (trimmed === '') {
        if (inList && listItems.length > 0) {
          elements.push(
            <ul key={`ul-${index}`} className="list-disc list-inside mb-4 space-y-2 text-gray-700">
              {listItems.map((item, i) => {
                const itemText = item.replace(/^[-*]\s+/, '')
                // Handle bold in list items
                const parts = itemText.split(/(\*\*[^*]+\*\*)/g)
                return (
                  <li key={i}>
                    {parts.map((part, pIndex) => 
                      part.startsWith('**') && part.endsWith('**') ? (
                        <strong key={pIndex}>{part.slice(2, -2)}</strong>
                      ) : part
                    )}
                  </li>
                )
              })}
            </ul>
          )
          listItems = []
          inList = false
        } else if (currentParagraph.length > 0) {
          const paraText = currentParagraph.join(' ')
          // Process links and bold
          const processed = paraText
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
              return `<a href="${url}" class="text-blue-600 hover:text-blue-700 underline"${url.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : ''}>${text}</a>`
            })
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
          
          elements.push(
            <p 
              key={`p-${index}`} 
              className="mb-4 text-gray-700 leading-7"
              dangerouslySetInnerHTML={{ __html: processed }}
            />
          )
          currentParagraph = []
        }
        return
      }

      // Regular text
      currentParagraph.push(trimmed)
    })

    // Handle remaining content
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key="ul-final" className="list-disc list-inside mb-4 space-y-2 text-gray-700">
          {listItems.map((item, i) => {
            const itemText = item.replace(/^[-*]\s+/, '')
            const parts = itemText.split(/(\*\*[^*]+\*\*)/g)
            return (
              <li key={i}>
                {parts.map((part, pIndex) => 
                  part.startsWith('**') && part.endsWith('**') ? (
                    <strong key={pIndex}>{part.slice(2, -2)}</strong>
                  ) : part
                )}
              </li>
            )
          })}
        </ul>
      )
    }

    if (currentParagraph.length > 0) {
      const paraText = currentParagraph.join(' ')
      const processed = paraText
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
          return `<a href="${url}" class="text-blue-600 hover:text-blue-700 underline"${url.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : ''}>${text}</a>`
        })
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      
      elements.push(
        <p 
          key="p-final" 
          className="mb-4 text-gray-700 leading-7"
          dangerouslySetInnerHTML={{ __html: processed }}
        />
      )
    }

    return elements
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link 
            href="/blog"
            className="text-blue-600 hover:text-blue-700 text-sm font-medium mb-4 inline-block"
          >
            ← Back to Blog
          </Link>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            {post.title}
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
            <span>By {post.author}</span>
            <span>•</span>
            <time dateTime={post.date}>
              {new Date(post.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </time>
          </div>
          <div className="flex flex-wrap gap-2 mt-4">
            {post.keywords.map((keyword) => (
              <span
                key={keyword}
                className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Article Content */}
      <article className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sm:p-8 lg:p-12">
          <div className="prose prose-lg max-w-none">
            {renderContent(post.content)}
          </div>
        </div>
      </article>

      {/* Related Posts */}
      {relatedPosts.length > 0 && (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Related Posts</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {relatedPosts.map((relatedPost) => (
              <Link
                key={relatedPost.slug}
                href={`/blog/${relatedPost.slug}`}
                className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2 hover:text-blue-600">
                  {relatedPost.title}
                </h3>
                <p className="text-gray-600 text-sm mb-3 line-clamp-2">{relatedPost.description}</p>
                <span className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                  Read more →
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* CTA Section */}
      <div className="bg-white border-t">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="bg-blue-50 rounded-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Ready to Convert Your Bank Statements?
            </h2>
            <p className="text-gray-600 mb-6">
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

