// An array of links for navigation bar
const navBarLinks: { name: string; url: string }[] = [];

// An array of links for footer
const footerLinks = [
  {
    section: 'Platform',
    links: [
      { name: 'Resolv DRS', url: '/' },
      { name: 'Architecture', url: '/#architecture' },
      { name: 'Use Cases', url: '/#use-cases' },
    ],
  },
  {
    section: 'Company',
    links: [
      { name: 'Resolv', url: '/company' },
      { name: 'Contact', url: '/contact' },
      { name: 'Privacy', url: '/privacy' },
    ],
  },
];

// An object of links for social icons
const socialLinks = {
  facebook: 'https://www.facebook.com/',
  x: 'https://twitter.com/',
  github: 'https://github.com/mearashadowfax/ScrewFast',
  google: 'https://www.google.com/',
  slack: 'https://slack.com/',
};

export default {
  navBarLinks,
  footerLinks,
  socialLinks,
};
