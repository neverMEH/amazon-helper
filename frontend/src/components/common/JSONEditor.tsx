import Editor from '@monaco-editor/react';
import { useRef, useState } from 'react';
import type { editor } from 'monaco-editor';
import { AlertCircle, CheckCircle } from 'lucide-react';

interface JSONEditorProps {
  value: any;
  onChange: (value: any) => void;
  height?: string;
  readOnly?: boolean;
  onMount?: (editor: editor.IStandaloneCodeEditor) => void;
}

export default function JSONEditor({ 
  value, 
  onChange, 
  height = '200px', 
  readOnly = false,
  onMount 
}: JSONEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const [isValid, setIsValid] = useState(true);
  const [error, setError] = useState<string>('');

  const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor) => {
    editorRef.current = editor;
    
    // Configure editor settings
    editor.updateOptions({
      minimap: { enabled: false },
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
    });

    if (onMount) {
      onMount(editor);
    }
  };

  const handleChange = (value: string | undefined) => {
    const newValue = value || '';
    
    // Validate JSON
    try {
      const parsed = JSON.parse(newValue || '{}');
      onChange(parsed);
      setIsValid(true);
      setError('');
    } catch (e) {
      // Still update the raw value so user can see what they're typing
      setIsValid(false);
      setError(e instanceof Error ? e.message : 'Invalid JSON');
    }
  };

  // Convert object to formatted JSON string
  const jsonString = typeof value === 'string' ? value : JSON.stringify(value, null, 2);

  return (
    <div>
      <div className="border border-gray-300 rounded-md overflow-hidden">
        <Editor
          height={height}
          defaultLanguage="json"
          language="json"
          value={jsonString}
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
        />
      </div>
      {!readOnly && (
        <div className="mt-2 flex items-center text-sm">
          {isValid ? (
            <div className="flex items-center text-green-600">
              <CheckCircle className="h-4 w-4 mr-1" />
              Valid JSON
            </div>
          ) : (
            <div className="flex items-center text-red-600">
              <AlertCircle className="h-4 w-4 mr-1" />
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}