import { useEffect, useRef } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';
import { editor } from 'monaco-editor';

interface QueryEditorProps {
  value: string;
  onChange: (value: string) => void;
  onParametersDetected?: (params: string[]) => void;
  height?: string;
  readOnly?: boolean;
}

export default function QueryEditor({
  value,
  onChange,
  onParametersDetected,
  height = '400px',
  readOnly = false,
}: QueryEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);

  useEffect(() => {
    // Detect parameters when value changes
    if (onParametersDetected) {
      const paramPattern = /\{\{(\w+)\}\}/g;
      const matches = [...value.matchAll(paramPattern)];
      const params = [...new Set(matches.map(m => m[1]))];
      onParametersDetected(params);
    }
  }, [value, onParametersDetected]);

  const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Configure SQL language features
    monaco.languages.registerCompletionItemProvider('sql', {
      provideCompletionItems: (model, position) => {
        const suggestions = [
          // AMC specific tables
          {
            label: 'impressions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'impressions',
            detail: 'AMC impressions table',
          },
          {
            label: 'clicks',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'clicks',
            detail: 'AMC clicks table',
          },
          {
            label: 'conversions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'conversions',
            detail: 'AMC conversions table',
          },
          {
            label: 'dsp_impressions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'dsp_impressions',
            detail: 'DSP impressions table',
          },
          {
            label: 'dsp_clicks',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'dsp_clicks',
            detail: 'DSP clicks table',
          },
          {
            label: 'sponsored_ads_impressions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'sponsored_ads_impressions',
            detail: 'Sponsored Ads impressions table',
          },
          {
            label: 'sponsored_ads_clicks',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'sponsored_ads_clicks',
            detail: 'Sponsored Ads clicks table',
          },
          // Common AMC columns
          {
            label: 'user_id',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'user_id',
            detail: 'User identifier',
          },
          {
            label: 'campaign_id',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'campaign_id',
            detail: 'Campaign identifier',
          },
          {
            label: 'impression_dt',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'impression_dt',
            detail: 'Impression datetime',
          },
          {
            label: 'click_dt',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'click_dt',
            detail: 'Click datetime',
          },
          {
            label: 'conversion_dt',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'conversion_dt',
            detail: 'Conversion datetime',
          },
          // Parameter template
          {
            label: '{{parameter}}',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: '{{${1:parameter_name}}}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            detail: 'Insert parameter placeholder',
          },
        ];

        return { suggestions };
      },
    });

    // Add custom theme
    monaco.editor.defineTheme('amc-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '569CD6' },
        { token: 'comment', foreground: '6A9955' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'number', foreground: 'B5CEA8' },
      ],
      colors: {
        'editor.background': '#1e1e1e',
        'editor.foreground': '#d4d4d4',
        'editorLineNumber.foreground': '#858585',
        'editor.selectionBackground': '#264f78',
        'editor.lineHighlightBackground': '#2a2a2a',
      },
    });

    monaco.editor.setTheme('amc-dark');

    // Format document on mount
    setTimeout(() => {
      editor.getAction('editor.action.formatDocument')?.run();
    }, 100);
  };

  const handleChange = (value: string | undefined) => {
    onChange(value || '');
  };

  return (
    <div className="border border-gray-300 rounded-md overflow-hidden">
      <Editor
        height={height}
        defaultLanguage="sql"
        value={value}
        onChange={handleChange}
        onMount={handleEditorDidMount}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          roundedSelection: false,
          scrollBeyondLastLine: false,
          readOnly,
          automaticLayout: true,
          formatOnPaste: true,
          formatOnType: true,
          suggestOnTriggerCharacters: true,
          wordWrap: 'on',
          wrappingStrategy: 'advanced',
          scrollbar: {
            vertical: 'visible',
            horizontal: 'visible',
          },
        }}
      />
    </div>
  );
}