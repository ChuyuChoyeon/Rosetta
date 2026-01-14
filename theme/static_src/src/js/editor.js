import { Editor } from 'bytemd';
import gfm from '@bytemd/plugin-gfm';
import highlight from '@bytemd/plugin-highlight';
import 'bytemd/dist/index.css';
import 'highlight.js/styles/github.css';

const plugins = [
  gfm(),
  highlight(),
];

window.initByteMD = function(elementId, inputId, initialValue) {
  const container = document.getElementById(elementId);
  const input = document.getElementById(inputId);
  
  if (!container || !input) return;

  const editor = new Editor({
    target: container,
    props: {
      value: initialValue || input.value || '',
      plugins: plugins,
    },
  });

  editor.$on('change', (e) => {
    editor.$set({ value: e.detail.value });
    input.value = e.detail.value;
  });

  return editor;
};
