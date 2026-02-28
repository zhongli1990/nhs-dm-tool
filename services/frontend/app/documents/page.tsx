"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, buildApiUrl, getTokenFromBrowser } from "../../lib/api";

type DocNode = {
  name: string;
  path: string;
  type: "dir" | "file";
  size_bytes: number;
  modified_at_utc: string;
  children?: DocNode[];
};

type DocContent = {
  name: string;
  path: string;
  suffix: string;
  size_bytes: number;
  modified_at_utc: string;
  is_text: boolean;
  content: string;
};

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderInlineMd(value: string): string {
  let out = escapeHtml(value);
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  return out;
}

function renderMarkdown(md: string): string {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const html: string[] = [];
  let inCode = false;
  let inUl = false;
  let inOl = false;

  const closeLists = () => {
    if (inUl) {
      html.push("</ul>");
      inUl = false;
    }
    if (inOl) {
      html.push("</ol>");
      inOl = false;
    }
  };

  for (const line of lines) {
    if (line.trim().startsWith("```")) {
      closeLists();
      if (!inCode) {
        html.push("<pre><code>");
        inCode = true;
      } else {
        html.push("</code></pre>");
        inCode = false;
      }
      continue;
    }

    if (inCode) {
      html.push(`${escapeHtml(line)}\n`);
      continue;
    }

    if (!line.trim()) {
      closeLists();
      html.push("<br />");
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      closeLists();
      const level = heading[1].length;
      html.push(`<h${level}>${renderInlineMd(heading[2])}</h${level}>`);
      continue;
    }

    const uItem = line.match(/^\s*[-*]\s+(.*)$/);
    if (uItem) {
      if (inOl) {
        html.push("</ol>");
        inOl = false;
      }
      if (!inUl) {
        html.push("<ul>");
        inUl = true;
      }
      html.push(`<li>${renderInlineMd(uItem[1])}</li>`);
      continue;
    }

    const oItem = line.match(/^\s*\d+\.\s+(.*)$/);
    if (oItem) {
      if (inUl) {
        html.push("</ul>");
        inUl = false;
      }
      if (!inOl) {
        html.push("<ol>");
        inOl = true;
      }
      html.push(`<li>${renderInlineMd(oItem[1])}</li>`);
      continue;
    }

    closeLists();
    html.push(`<p>${renderInlineMd(line)}</p>`);
  }

  closeLists();
  if (inCode) html.push("</code></pre>");
  return html.join("\n");
}

function firstDocumentPath(node: DocNode | null): string {
  if (!node) return "";
  if (node.type === "file") return node.path;
  for (const child of node.children || []) {
    const hit = firstDocumentPath(child);
    if (hit) return hit;
  }
  return "";
}

function parentDir(path: string): string {
  if (!path) return "";
  const bits = path.split("/").filter(Boolean);
  bits.pop();
  return bits.join("/");
}

function DocTree({ node, selected, onSelect }: { node: DocNode; selected: string; onSelect: (path: string, type: "file" | "dir") => void }) {
  const isActive = selected === node.path;
  return (
    <li>
      <button
        type="button"
        className={isActive ? "doc-node active" : "doc-node"}
        onClick={() => onSelect(node.path, node.type)}
      >
        {node.type === "dir" ? "[DIR]" : "[FILE]"} {node.name}
      </button>
      {node.type === "dir" && node.children && node.children.length > 0 ? (
        <ul className="doc-tree-list">
          {node.children.map((child) => (
            <DocTree key={`${node.path}/${child.name}`} node={child} selected={selected} onSelect={onSelect} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export default function DocumentsPage() {
  const [tree, setTree] = useState<DocNode | null>(null);
  const [selectedPath, setSelectedPath] = useState("");
  const [content, setContent] = useState<DocContent | null>(null);
  const [message, setMessage] = useState("");
  const [uploadDir, setUploadDir] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [replaceUpload, setReplaceUpload] = useState(false);

  async function loadTree() {
    const payload = await apiGet<{ tree: DocNode }>("/api/docs/tree");
    setTree(payload.tree);
    const fallback = selectedPath || firstDocumentPath(payload.tree);
    if (fallback) {
      setSelectedPath(fallback);
      await loadContent(fallback);
      setUploadDir(parentDir(fallback));
    }
  }

  async function loadContent(path: string) {
    const payload = await apiGet<DocContent>(`/api/docs/content?path=${encodeURIComponent(path)}`);
    setContent(payload);
  }

  useEffect(() => {
    loadTree().catch((ex) => setMessage(ex.message || "Failed to load documents."));
  }, []);

  async function handleSelect(path: string, type: "file" | "dir") {
    if (type === "dir") {
      setUploadDir(path);
      setSelectedPath(path);
      return;
    }
    setSelectedPath(path);
    setUploadDir(parentDir(path));
    await loadContent(path);
  }

  async function handleDownload(path: string) {
    const token = getTokenFromBrowser();
    const res = await fetch(buildApiUrl(`/api/docs/download?path=${encodeURIComponent(path)}`), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`Download failed: ${res.status}`);
    const blob = await res.blob();
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = path.split("/").pop() || "document";
    a.click();
    URL.revokeObjectURL(href);
  }

  async function handleUpload() {
    if (!uploadFile) {
      setMessage("Select a file to upload.");
      return;
    }
    const form = new FormData();
    form.set("target_dir", uploadDir);
    form.set("replace", replaceUpload ? "true" : "false");
    form.set("file", uploadFile);

    const token = getTokenFromBrowser();
    const res = await fetch(buildApiUrl("/api/docs/upload"), {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(payload?.detail || `Upload failed: ${res.status}`);
    }
    setMessage(`Uploaded ${payload?.name || uploadFile.name}.`);
    setUploadFile(null);
    await loadTree();
  }

  const renderedMarkdown = useMemo(() => {
    if (!content || !content.is_text) return "";
    if (content.suffix !== ".md") return `<pre>${escapeHtml(content.content)}</pre>`;
    return renderMarkdown(content.content);
  }, [content]);

  return (
    <main className="grid" style={{ gridTemplateColumns: "1fr" }}>
      <section className="card">
        <h3>SaaS Platform Documents</h3>
        <div className="muted">Browse docs folder structure, view markdown guides, and upload/download controlled artifacts.</div>
        {message ? <p className="status-pass">{message}</p> : null}
      </section>

      <section className="card docs-layout">
        <aside className="docs-sidebar">
          <h4>Document Tree</h4>
          <div className="muted">Root: docs/</div>
          <ul className="doc-tree-list">
            {tree ? <DocTree node={tree} selected={selectedPath} onSelect={(p, t) => handleSelect(p, t).catch((ex) => setMessage(ex.message))} /> : null}
          </ul>
        </aside>

        <section className="docs-content">
          <div className="docs-toolbar">
            <div>
              <h4>{content?.name || "Select a document"}</h4>
              <div className="muted">{content?.path || ""}</div>
            </div>
            {content ? (
              <button type="button" className="primary" onClick={() => handleDownload(content.path).catch((ex) => setMessage(ex.message))}>
                Download
              </button>
            ) : null}
          </div>
          <div className="doc-viewer">
            {content ? (
              content.is_text ? (
                <article className="doc-markdown" dangerouslySetInnerHTML={{ __html: renderedMarkdown }} />
              ) : (
                <div className="muted">Binary/unsupported preview. Use Download.</div>
              )
            ) : (
              <div className="muted">No document selected.</div>
            )}
          </div>
        </section>
      </section>

      <section className="card">
        <h4>Upload Document</h4>
        <div className="controls">
          <label>
            Target directory
            <input value={uploadDir} onChange={(e) => setUploadDir(e.target.value)} placeholder="analysis" />
          </label>
          <label>
            Select file
            <input type="file" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} />
          </label>
          <label>
            Replace if exists
            <select value={replaceUpload ? "yes" : "no"} onChange={(e) => setReplaceUpload(e.target.value === "yes")}>
              <option value="no">No</option>
              <option value="yes">Yes</option>
            </select>
          </label>
          <label style={{ alignSelf: "end" }}>
            <button type="button" className="primary" onClick={() => handleUpload().catch((ex) => setMessage(ex.message))}>
              Upload
            </button>
          </label>
        </div>
      </section>
    </main>
  );
}
