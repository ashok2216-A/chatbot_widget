/**
 * Lightweight Markdown → HTML renderer (zero dependencies).
 * Handles: headings, bold, italic, inline code, fenced code blocks,
 *          bullet lists, numbered lists, horizontal rules, links.
 */
export function formatText(text) {
  if (!text) return '';

  const lines = text.split(/\r?\n/);
  const output = [];
  let currentBlock = null; // 'ul', 'ol', 'code', 'blockquote', 'p'
  let codeLines = [];
  let codeLang = '';

  const closeBlock = () => {
    if (currentBlock === 'ul') output.push('</ul>');
    if (currentBlock === 'ol') output.push('</ol>');
    if (currentBlock === 'blockquote') output.push('</blockquote>');
    if (currentBlock === 'p') output.push('</p>');
    if (currentBlock === 'code') {
      const escaped = codeLines.join('\n')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      output.push(`<pre class="md-codeblock"><code class="lang-${codeLang}">${escaped}</code></pre>`);
      codeLines = [];
      codeLang = '';
    }
    currentBlock = null;
  };

  const inline = (str) => str
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/`([^`]+)`/g, '<code class="md-code">$1</code>')
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="md-link">$1</a>');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // ── Code Blocks ──
    if (/^```/.test(trimmed)) {
      if (currentBlock !== 'code') {
        closeBlock();
        codeLang = trimmed.replace(/^```/, '').trim() || 'text';
        currentBlock = 'code';
      } else {
        closeBlock();
      }
      continue;
    }
    if (currentBlock === 'code') {
      codeLines.push(line);
      continue;
    }

    // ── Blank Lines ──
    if (trimmed === '') {
      closeBlock();
      continue;
    }

    // ── Headings ──
    const h = line.match(/^(#{1,6})\s+(.+)/);
    if (h) {
      closeBlock();
      const level = h[1].length;
      output.push(`<h${level} class="md-h${level}">${inline(h[2])}</h${level}>`);
      continue;
    }

    // ── Horizontal Rules ──
    if (/^---+$/.test(trimmed) || /^\*\*\*+$/.test(trimmed)) {
      closeBlock();
      output.push('<hr class="md-hr" />');
      continue;
    }

    // ── Blockquotes ──
    if (/^>\s?/.test(trimmed)) {
      if (currentBlock !== 'blockquote') {
        closeBlock();
        output.push('<blockquote class="md-blockquote">');
        currentBlock = 'blockquote';
      }
      output.push(inline(trimmed.replace(/^>\s?/, '')) + '<br/>');
      continue;
    }

    // ── Unordered Lists ──
    const ul = line.match(/^[\s]*[-*+]\s+(.+)/);
    if (ul) {
      if (currentBlock !== 'ul') {
        closeBlock();
        output.push('<ul class="md-ul">');
        currentBlock = 'ul';
      }
      output.push(`<li class="md-li">${inline(ul[1])}</li>`);
      continue;
    }

    // ── Ordered Lists ──
    const ol = line.match(/^[\s]*\d+[.)]\s+(.+)/);
    if (ol) {
      if (currentBlock !== 'ol') {
        closeBlock();
        output.push('<ol class="md-ol">');
        currentBlock = 'ol';
      }
      output.push(`<li class="md-li">${inline(ol[1])}</li>`);
      continue;
    }

    // ── Paragraphs ──
    if (currentBlock !== 'p') {
      closeBlock();
      output.push('<p class="md-paragraph">');
      currentBlock = 'p';
    } else {
      output.push('<br/>');
    }
    output.push(inline(line));
  }

  closeBlock();
  return output.join('\n');
}
