import ogImageSrc from '@images/social.png';

export const SITE = {
  title: 'Resolv',
  tagline: 'Autonomous Supply Chain Resilience',
  description:
    'Resolv DRS helps manufacturers detect disruption risk early, model business impact, and execute mitigation workflows with explainable AI.',
  description_short:
    'Resolv DRS detects risk, models impact, and launches mitigation workflows.',
  url: 'https://resolv.ai',
  author: 'Resolv',
};

export const SEO = {
  title: SITE.title,
  description: SITE.description,
  structuredData: {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    inLanguage: 'en-US',
    '@id': SITE.url,
    url: SITE.url,
    name: SITE.title,
    description: SITE.description,
    isPartOf: {
      '@type': 'WebSite',
      url: SITE.url,
      name: SITE.title,
      description: SITE.description,
    },
  },
};

export const OG = {
  locale: 'en_US',
  type: 'website',
  url: SITE.url,
  title: `${SITE.title}: Autonomous Supply Chain Resilience`,
  description:
    'Resolv DRS tracks leading global signals, quantifies disruption exposure, and helps teams deploy mitigation workflows faster.',
  image: ogImageSrc,
};

export const partnersData = [];
