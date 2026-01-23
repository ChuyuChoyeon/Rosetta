import { Viewer } from 'bytemd';
import gfm from '@bytemd/plugin-gfm';
import highlight from '@bytemd/plugin-highlight';
import breaks from '@bytemd/plugin-breaks';
import gemoji from '@bytemd/plugin-gemoji';
import mediumZoom from '@bytemd/plugin-medium-zoom';
import math from '@bytemd/plugin-math';
import mermaid from '@bytemd/plugin-mermaid';

import 'bytemd/dist/index.css';
import 'highlight.js/styles/github.css';
import 'katex/dist/katex.css';

const plugins = [
  gfm(),
  highlight(),
  breaks(),
  gemoji(),
  mediumZoom(),
  math(),
  mermaid(),
];

const injectStyles = () => {
    if (document.getElementById('bytemd-viewer-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'bytemd-viewer-styles';
    style.textContent = `
        .markdown-body {
            font-family: inherit !important;
            color: inherit !important;
            background-color: transparent !important;
            font-size: 1rem;
            line-height: 1.75;
        }
        
        /* Dark Mode Adaptation */
        :root[data-theme="dark"] .markdown-body,
        html.dark .markdown-body {
            color: #a6adbb !important;
        }
        
        :root[data-theme="dark"] .markdown-body code,
        html.dark .markdown-body code {
            background-color: #191e24 !important;
            color: #a6adbb !important;
        }
        
        :root[data-theme="dark"] .markdown-body pre,
        html.dark .markdown-body pre {
            background-color: #0d1117 !important;
        }

        /* Adjustments for DaisyUI Prose conflict */
        .prose .markdown-body {
            max-width: none;
        }
        
        /* Math Formula sizing */
        .katex {
            font-size: 1.1em;
        }
    `;
    document.head.appendChild(style);
};

window.initByteMDViewer = function(elementId, content) {
  const container = document.getElementById(elementId);
  if (!container) return;

  injectStyles();

  new Viewer({
    target: container,
    props: {
      value: content,
      plugins: plugins,
    },
  });
};
