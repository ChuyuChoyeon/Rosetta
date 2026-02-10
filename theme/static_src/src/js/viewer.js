import { Viewer } from "bytemd";
import gfm from "@bytemd/plugin-gfm";
import highlight from "@bytemd/plugin-highlight";
import breaks from "@bytemd/plugin-breaks";
import gemoji from "@bytemd/plugin-gemoji";
import mediumZoom from "@bytemd/plugin-medium-zoom";
import math from "@bytemd/plugin-math";
import mermaid from "@bytemd/plugin-mermaid";

import "bytemd/dist/index.css";
import "highlight.js/styles/github.css";
import "katex/dist/katex.css";

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
  if (document.getElementById("bytemd-viewer-styles")) return;

  const style = document.createElement("style");
  style.id = "bytemd-viewer-styles";
  style.textContent = `
        .markdown-body {
            font-family: inherit !important;
            color: inherit !important;
            background-color: transparent !important;
            font-size: 1rem;
            line-height: 1.75;
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

window.initByteMDViewer = function (elementId, content) {
  const container = document.getElementById(elementId);
  if (!container) return;

  injectStyles();

  // Dark mode support for Mermaid
  const isDark =
    document.documentElement.getAttribute("data-theme") === "dark" ||
    document.documentElement.classList.contains("dark");

  if (isDark) {
    // Try to configure mermaid if available globally or via plugin
    // ByteMD's mermaid plugin usually renders SVGs directly.
    // We can try to force dark theme via mermaid API if exposed,
    // but often CSS overrides are more reliable for SVGs.
  }

  new Viewer({
    target: container,
    props: {
      value: content,
      plugins: plugins,
    },
  });
};
