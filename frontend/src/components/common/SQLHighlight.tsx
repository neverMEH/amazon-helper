interface SQLHighlightProps {
  sql: string;
  className?: string;
}

export default function SQLHighlight({ sql, className = '' }: SQLHighlightProps) {
  // SQL keywords for highlighting
  const keywords = [
    'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON',
    'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'WITH', 'UNION',
    'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CREATE', 'TABLE',
    'ALTER', 'DROP', 'INDEX', 'VIEW', 'TRIGGER', 'PROCEDURE', 'FUNCTION',
    'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AND', 'OR', 'NOT', 'IN', 'EXISTS',
    'BETWEEN', 'LIKE', 'IS', 'NULL', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN',
    'MAX', 'CAST', 'CONVERT', 'COALESCE', 'NULLIF', 'PARTITION', 'OVER',
    'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'LAG', 'LEAD', 'FIRST_VALUE', 'LAST_VALUE'
  ];

  const functions = [
    'DATE', 'DATETIME', 'TIMESTAMP', 'EXTRACT', 'DATE_ADD', 'DATE_SUB', 'DATEDIFF',
    'SUBSTRING', 'CONCAT', 'LENGTH', 'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM',
    'REPLACE', 'ROUND', 'FLOOR', 'CEILING', 'ABS', 'MOD', 'POWER', 'SQRT'
  ];

  const highlightSQL = (query: string) => {
    let highlighted = query;

    // Escape HTML
    highlighted = highlighted
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Highlight strings (single quotes)
    highlighted = highlighted.replace(
      /'([^']*)'/g,
      '<span class="text-green-400">\'$1\'</span>'
    );

    // Highlight strings (double quotes for identifiers)
    highlighted = highlighted.replace(
      /"([^"]*)"/g,
      '<span class="text-green-400">"$1"</span>'
    );

    // Highlight numbers
    highlighted = highlighted.replace(
      /\b(\d+\.?\d*)\b/g,
      '<span class="text-purple-400">$1</span>'
    );

    // Highlight comments
    highlighted = highlighted.replace(
      /--.*$/gm,
      '<span class="text-gray-500">$&</span>'
    );

    // Highlight parameters ({{param}})
    highlighted = highlighted.replace(
      /\{\{([^}]+)\}\}/g,
      '<span class="text-yellow-400 font-bold">{{$1}}</span>'
    );

    // Highlight keywords (case-insensitive)
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b`, 'gi');
      highlighted = highlighted.replace(
        regex,
        '<span class="text-blue-400 font-semibold">$1</span>'
      );
    });

    // Highlight functions
    functions.forEach(func => {
      const regex = new RegExp(`\\b(${func})\\b`, 'gi');
      highlighted = highlighted.replace(
        regex,
        '<span class="text-cyan-400">$1</span>'
      );
    });

    // Highlight operators
    highlighted = highlighted.replace(
      /(\+|-|\*|\/|=|!=|<>|<=|>=|<|>)/g,
      '<span class="text-orange-400">$1</span>'
    );

    return highlighted;
  };

  return (
    <pre className={`bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-xs ${className}`}>
      <code dangerouslySetInnerHTML={{ __html: highlightSQL(sql) }} />
    </pre>
  );
}