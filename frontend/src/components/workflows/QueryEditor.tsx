import { useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import type { Monaco } from '@monaco-editor/react';
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
      provideCompletionItems: () => {
        const suggestions: any[] = [
          // AMC specific tables - DSP
          {
            label: 'dsp_impressions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'dsp_impressions',
            detail: 'DSP display impressions with campaign_id, user_id, impression_dt',
          },
          {
            label: 'dsp_clicks',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'dsp_clicks',
            detail: 'DSP display clicks with campaign_id, user_id, click_dt',
          },
          {
            label: 'dsp_conversions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'dsp_conversions',
            detail: 'DSP conversions with campaign_id, conversion_dt, conversion_value',
          },
          // Sponsored Ads tables
          {
            label: 'sponsored_ads_impressions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'sponsored_ads_impressions',
            detail: 'Sponsored Ads impressions (SP/SB/SD) with campaign_id, ad_type, user_id',
          },
          {
            label: 'sponsored_ads_clicks',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'sponsored_ads_clicks',
            detail: 'Sponsored Ads clicks (SP/SB/SD) with campaign_id, ad_type, user_id',
          },
          {
            label: 'sb_impressions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'sb_impressions',
            detail: 'Sponsored Brands specific impressions',
          },
          {
            label: 'sb_clicks',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'sb_clicks',
            detail: 'Sponsored Brands specific clicks',
          },
          {
            label: 'sd_impressions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'sd_impressions',
            detail: 'Sponsored Display specific impressions',
          },
          {
            label: 'sd_clicks',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'sd_clicks',
            detail: 'Sponsored Display specific clicks',
          },
          // Generic tables (legacy)
          {
            label: 'impressions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'impressions',
            detail: 'Generic impressions table (legacy)',
          },
          {
            label: 'clicks',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'clicks',
            detail: 'Generic clicks table (legacy)',
          },
          {
            label: 'conversions',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'conversions',
            detail: 'Generic conversions table (legacy)',
          },
          // Common AMC columns
          {
            label: 'user_id',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'user_id',
            detail: 'Anonymized user identifier',
          },
          {
            label: 'campaign_id',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'campaign_id',
            detail: 'Numeric campaign identifier',
          },
          {
            label: 'campaign_name',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'campaign_name',
            detail: 'Human-readable campaign name',
          },
          {
            label: 'advertiser_id',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'advertiser_id',
            detail: 'Advertiser account ID',
          },
          {
            label: 'ad_type',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'ad_type',
            detail: 'Ad type: SP, SB, or SD',
          },
          {
            label: 'asin',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'asin',
            detail: 'Amazon Standard Identification Number',
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
          {
            label: 'event_type',
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: 'event_type',
            detail: 'Event type: impression, click, conversion',
          },
          // Parameter template
          {
            label: '{{parameter}}',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: '{{${1:parameter_name}}}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            detail: 'Insert parameter placeholder',
          },
          // Common date parameters
          {
            label: '{{start_date}}',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: '{{start_date}}',
            detail: 'Start date parameter (YYYY-MM-DD)',
          },
          {
            label: '{{end_date}}',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: '{{end_date}}',
            detail: 'End date parameter (YYYY-MM-DD)',
          },
          // AMC Privacy threshold
          {
            label: 'HAVING COUNT(DISTINCT user_id) >= 10',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'HAVING COUNT(DISTINCT user_id) >= 10',
            detail: 'AMC privacy threshold requirement',
          },
          // Common query patterns
          {
            label: 'DSP Campaign Query',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: `SELECT 
    campaign_id,
    campaign_name,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) as impressions,
    SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as clicks
FROM dsp_impressions
WHERE impression_dt >= '{{start_date}}' 
  AND impression_dt <= '{{end_date}}'
GROUP BY campaign_id, campaign_name
HAVING COUNT(DISTINCT user_id) >= 10`,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            detail: 'DSP campaign performance template',
          },
          {
            label: 'Sponsored Ads Query',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: `SELECT 
    campaign_id,
    campaign_name,
    ad_type,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) as impressions
FROM sponsored_ads_impressions
WHERE impression_dt >= '{{start_date}}' 
  AND impression_dt <= '{{end_date}}'
  AND ad_type IN ('SP', 'SB', 'SD')
GROUP BY campaign_id, campaign_name, ad_type
HAVING COUNT(DISTINCT user_id) >= 10`,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            detail: 'Sponsored Ads performance template',
          },
        ];

        return { suggestions } as any;
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