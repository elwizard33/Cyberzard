import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// Custom domain for documentation
const site = 'https://docs.cyberzard.com';

export default defineConfig({
  site,
  // No base path needed with custom domain
  integrations: [
    starlight({
      title: 'Docs',
      description: 'AI-assisted CyberPanel security CLI documentation',
      logo: {
        src: './src/assets/cyberzard-logo.png',
        alt: 'Cyberzard',
      },
  // Load site-wide style overrides (e.g., tweak TOC width)
  customCss: ['./src/styles/overrides.css'],
      social: [
        { label: 'GitHub', href: 'https://github.com/elwizard33/Cyberzard', icon: 'github' }
      ],
      sidebar: [
        {
          label: 'Getting Started',
          items: [
            { label: 'Installation', link: '/installation/' },
            { label: 'Commands', link: '/commands/' },
            { label: 'n8n Setup', link: '/n8n-setup/' },
            { label: 'Chat mode', link: '/chat/' },
            { label: 'Configuration', link: '/configuration/' },
          ],
        },
        {
          label: 'How it works',
          items: [
            { label: 'AI & Agent', link: '/ai-and-agent/' },
            { label: 'Architecture', link: '/architecture/' },
            { label: 'Remediation', link: '/remediation/' },
            { label: 'Security Model', link: '/security/' },
          ],
        },
        {
          label: 'Project',
          items: [
            { label: 'FAQ', link: '/faq/' },
            { label: 'Roadmap', link: '/roadmap/' },
          ],
        },
      ],
    })
  ]
});
