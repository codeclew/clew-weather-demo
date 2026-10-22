import {language, t} from './src/components/clew-locale.js';

const generatorRevision = /^[a-f0-9]{40}$/.test(process.env.CODECLEW_DOCS_GENERATOR_REVISION || '') ? process.env.CODECLEW_DOCS_GENERATOR_REVISION : null;

export default {
  title: t('Codeclew documentation'),
  i18n: {defaultLocale: language, locales: [language]},
  url: process.env.CODECLEW_DOCS_URL || 'https://example.invalid',
  baseUrl: process.env.CODECLEW_DOCS_BASE_URL || '/',
  trailingSlash: false,
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {mermaid: true, hooks: {onBrokenMarkdownLinks: 'throw'}},
  themes: ['@docusaurus/theme-mermaid'],
  presets: [['classic', {docs: {routeBasePath: '/', sidebarPath: './sidebars.js'}, blog: false, theme: {customCss: './src/css/clew.css'}}]],
  themeConfig: {
    ...(generatorRevision ? {announcementBar: {id: 'renderer-candidate', content: `Renderer review candidate · source commit <code>${generatorRevision}</code> · retained source evidence; no new runtime observation`, isCloseable: false}} : {}),
    navbar: {title: 'Codeclew', items: [
      {to: '/', label: t('Overview'), position: 'left', exact: true},
      {to: '/catalog', label: t('Browse'), position: 'left'},
      ...(process.env.CODECLEW_DOCS_REVIEW_INDEX === 'true' ? [{to: '/review', label: 'Review index', position: 'left'}] : []),
      {to: '/help', label: t('Help'), position: 'right'},
      {to: '/runbooks', label: t('Author runbooks'), position: 'right'},
      {to: '/history', label: t('Publication details'), position: 'right'},
      {type: 'custom-clewSearch', position: 'right'},
    ]},
    colorMode: {defaultMode: 'light', disableSwitch: true},
    mermaid: {options: {securityLevel: 'strict', fontSize: 16}},
  },
};
