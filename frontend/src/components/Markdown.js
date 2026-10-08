import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// [[Nota]] wiki-links become #note:<slug> links handled by onNoteClick
const slugify = (s) =>
  s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

export default function Markdown({ children, onNoteClick }) {
  const text = (children || '').replace(/\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]/g,
    (_, title) => `[${title}](#note:${slugify(title)})`);
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children: kids }) => {
            if (href && href.startsWith('#note:')) {
              return (
                <a href={href} className="wiki-link"
                   onClick={(e) => { e.preventDefault(); onNoteClick && onNoteClick(href.slice(6)); }}>
                  {kids}
                </a>
              );
            }
            return <a href={href} target="_blank" rel="noreferrer">{kids}</a>;
          },
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
