import Editor from '@monaco-editor/react';
import { useRef } from 'react';
import type { editor } from 'monaco-editor';

interface SQLEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: string;
  readOnly?: boolean;
  onMount?: (editor: editor.IStandaloneCodeEditor) => void;
}

export default function SQLEditor({ 
  value, 
  onChange, 
  height = '400px', 
  readOnly = false,
  onMount 
}: SQLEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  // Debug logging
  console.log('SQLEditor rendering with value length:', value?.length || 0, 'readOnly:', readOnly);

  const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor) => {
    editorRef.current = editor;
    
    // Configure editor settings
    editor.updateOptions({
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      fontSize: 14,
      lineNumbers: 'on',
      renderWhitespace: 'selection',
      scrollbar: {
        vertical: 'visible',
        horizontal: 'visible',
        verticalScrollbarSize: 10,
        horizontalScrollbarSize: 10,
      },
      suggestOnTriggerCharacters: true,
      acceptSuggestionOnCommitCharacter: true,
      acceptSuggestionOnEnter: 'on',
      quickSuggestions: {
        other: true,
        comments: false,
        strings: false
      },
      parameterHints: {
        enabled: true
      },
      suggest: {
        showKeywords: true,
        showSnippets: true,
      }
    });

    // Add custom SQL completions
    const monaco = (window as any).monaco;
    if (monaco) {
      // Register SQL keywords for better autocomplete
      monaco.languages.registerCompletionItemProvider('sql', {
        provideCompletionItems: () => {
          const suggestions = [
            // AMC specific functions
            'ARRAY_AGG', 'ARRAY_INTERSECT', 'ARRAY_LENGTH', 'CARDINALITY',
            'DATE_TRUNC', 'STRUCT', 
            // Common SQL keywords
            'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
            'JOIN', 'LEFT JOIN', 'INNER JOIN', 'ON', 'AS', 'WITH',
            'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN',
            'DISTINCT', 'LIMIT', 'OFFSET',
            // AMC specific tables
            'impressions', 'clicks', 'conversions', 'impressions_clicks_conversions'
          ].map(keyword => ({
            label: keyword,
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: keyword,
            range: null
          }));

          return { suggestions };
        }
      });
    }

    if (onMount) {
      onMount(editor);
    }
  };

  const handleChange = (value: string | undefined) => {
    onChange(value || '');
  };

  // Fallback if Monaco fails to load
  if (!value && !readOnly) {
    return (
      <div className="border border-gray-300 rounded-md p-4 bg-gray-50">
        <p className="text-gray-500">No SQL query content</p>
      </div>
    );
  }

  return (
    <div className="border border-gray-300 rounded-md overflow-hidden">
      <Editor
        height={height}
        defaultLanguage="sql"
        language="sql"
        value={value}
        onChange={handleChange}
        onMount={handleEditorDidMount}
        theme="vs-light"
        options={{
          readOnly,
          automaticLayout: true,
          formatOnType: true,
          formatOnPaste: true,
          wordWrap: 'on',
          wrappingIndent: 'indent',
        }}
        loading={
          <div className="flex items-center justify-center h-full bg-gray-50">
            <p className="text-gray-500">Loading SQL editor...</p>
          </div>
        }
      />
    </div>
  );
}