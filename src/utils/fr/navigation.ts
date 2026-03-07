const navBarLinks: { name: string; url: string }[] = [];

const footerLinks = [
  {
    section: 'Plateforme',
    links: [
      { name: 'Resolv DRS', url: '/fr' },
      { name: 'Architecture', url: '/fr#architecture' },
      { name: "Cas d'usage", url: '/fr#use-cases' },
    ],
  },
  {
    section: 'Entreprise',
    links: [
      { name: 'Resolv', url: '/fr/company' },
      { name: 'Contact', url: '/fr/contact' },
      { name: 'Confidentialite', url: '/fr/privacy' },
    ],
  },
];

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
