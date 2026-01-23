import { Editor } from 'bytemd';
import gfm from '@bytemd/plugin-gfm';
import highlight from '@bytemd/plugin-highlight';
import breaks from '@bytemd/plugin-breaks';
import gemoji from '@bytemd/plugin-gemoji';
import mediumZoom from '@bytemd/plugin-medium-zoom';
import math from '@bytemd/plugin-math';
import mermaid from '@bytemd/plugin-mermaid';

import zhHans from 'bytemd/locales/zh_Hans.json';
import gfmZhHans from '@bytemd/plugin-gfm/locales/zh_Hans.json';
import mathZhHans from '@bytemd/plugin-math/locales/zh_Hans.json';
import mermaidZhHans from '@bytemd/plugin-mermaid/locales/zh_Hans.json';

import 'bytemd/dist/index.css';
import 'highlight.js/styles/github.css';
import 'katex/dist/katex.css';

const plugins = [
  gfm({ locale: gfmZhHans }),
  highlight(),
  breaks(),
  gemoji(),
  mediumZoom(),
  math({ locale: mathZhHans }),
  mermaid({ locale: mermaidZhHans }),
];

const injectStyles = () => {
    if (document.getElementById('bytemd-static-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'bytemd-static-styles';
    style.textContent = `
        .bytemd {
            height: 70vh;
            min-height: 500px;
            border-radius: 0.5rem;
        }

        .bytemd-fullscreen {
            z-index: 10000 !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            height: 100vh !important;
            width: 100vw !important;
            background-color: #ffffff;
            display: flex !important;
            flex-direction: column !important;
        }

        .bytemd-fullscreen .bytemd-body {
            flex: 1 !important;
            height: auto !important;
        }
        
        :root[data-theme="dark"] .bytemd,
        html.dark .bytemd {
            --bytemd-bg: #1d232a;
            --bytemd-border: #2a323c;
            --bytemd-text: #a6adbb;
            --bytemd-toolbar-bg: #191e24;
            
            background-color: var(--bytemd-bg);
            border-color: var(--bytemd-border);
            color: var(--bytemd-text);
        }

        :root[data-theme="dark"] .bytemd-fullscreen,
        html.dark .bytemd-fullscreen {
            background-color: var(--bytemd-bg) !important;
        }

        :root[data-theme="dark"] .bytemd-toolbar,
        html.dark .bytemd-toolbar {
            background-color: var(--bytemd-toolbar-bg) !important;
            border-bottom-color: var(--bytemd-border) !important;
            color: var(--bytemd-text) !important;
        }
        
        :root[data-theme="dark"] .bytemd-toolbar-icon,
        html.dark .bytemd-toolbar-icon {
            color: var(--bytemd-text) !important;
        }
        :root[data-theme="dark"] .bytemd-toolbar-icon:hover,
        html.dark .bytemd-toolbar-icon:hover {
            background-color: var(--bytemd-border) !important;
        }

        :root[data-theme="dark"] .bytemd-status,
        html.dark .bytemd-status {
            background-color: var(--bytemd-toolbar-bg) !important;
            border-top-color: var(--bytemd-border) !important;
            color: var(--bytemd-text) !important;
        }

        :root[data-theme="dark"] .bytemd-body,
        html.dark .bytemd-body {
            background-color: var(--bytemd-bg) !important;
        }
        
        :root[data-theme="dark"] .CodeMirror,
        html.dark .CodeMirror {
            background-color: var(--bytemd-bg) !important;
            color: var(--bytemd-text) !important;
        }
        :root[data-theme="dark"] .CodeMirror-cursor,
        html.dark .CodeMirror-cursor {
            border-left-color: var(--bytemd-text) !important;
        }

        :root[data-theme="dark"] .markdown-body,
        html.dark .markdown-body {
            color: var(--bytemd-text) !important;
            background-color: var(--bytemd-bg) !important;
            font-family: inherit !important;
        }
        
        :root[data-theme="dark"] .markdown-body code,
        html.dark .markdown-body code {
            background-color: var(--bytemd-toolbar-bg) !important;
            color: var(--bytemd-text) !important;
        }
        
        :root[data-theme="dark"] .markdown-body pre,
        html.dark .markdown-body pre {
            background-color: #0d1117 !important;
        }
    `;
    document.head.appendChild(style);
};

window.initByteMD = function(elementId, inputId, initialValue) {
  const container = document.getElementById(elementId);
  const input = document.getElementById(inputId);
  
  if (!container) return;

  injectStyles();

  const editor = new Editor({
    target: container,
    props: {
      value: initialValue || (input ? input.value : '') || '',
      plugins: plugins,
      locale: zhHans,
      uploadImages: async (files) => {
        const results = [];
        for (const file of files) {
            const formData = new FormData();
            formData.append('image', file);
            try {
                const response = await fetch('/upload/image/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1]
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    results.push({
                        url: data.url,
                        title: file.name,
                        alt: file.name
                    });
                }
            } catch (e) {
                console.error(e);
            }
        }
        return results;
      }
    },
  });

  if (input) {
      editor.$on('change', (e) => {
        editor.$set({ value: e.detail.value });
        input.value = e.detail.value;
      });
  }

  const bytemdElement = container.querySelector('.bytemd');
  if (bytemdElement) {
      const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
              if (mutation.attributeName === 'class') {
                  if (bytemdElement.classList.contains('bytemd-fullscreen')) {
                      document.body.style.overflow = 'hidden';
                  } else {
                      document.body.style.overflow = '';
                  }
              }
          });
      });
      observer.observe(bytemdElement, { attributes: true });
  }

  return editor;
};
