// Additive website navigation; the frozen exporter-owned config stays unchanged.
import frozen from '../docusaurus/project/docusaurus.config.js';
import {createRequire} from 'node:module';
const require = createRequire(new URL('../docusaurus/project/package.json', import.meta.url));

export default {
  ...frozen,
  presets: [[require.resolve('@docusaurus/preset-classic'), frozen.presets[0][1]]],
  themes: [require.resolve('@docusaurus/theme-mermaid')],
  themeConfig: {
    ...frozen.themeConfig,
    navbar: {
      ...frozen.themeConfig.navbar,
      items: [
        ...frozen.themeConfig.navbar.items,
        {href: 'pathname:///clew-weather-demo/rendering/', label: 'Rendering showcase', position: 'left', prependBaseUrlToHref: false, autoAddBaseUrl: false, target: '_self'},
      ],
    },
  },
};
