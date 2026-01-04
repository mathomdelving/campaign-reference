import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/api/', '/reset-password', '/unsubscribe', '/settings'],
    },
    sitemap: 'https://campaign-reference.com/sitemap.xml',
  };
}
