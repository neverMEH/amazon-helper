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
    // First, escape HTML to prevent XSS
    let highlighted = query
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Store comments and their positions to handle them separately
    const commentMatches: Array<{start: number, end: number, content: string}> = [];
    const commentRegex = /--.*$/gm;
    let match;
    
    while ((match = commentRegex.exec(highlighted)) !== null) {
      commentMatches.push({
        start: match.index,
        end: match.index + match[0].length,
        content: match[0]
      });
    }
    
    // Function to check if a position is inside a comment
    const isInComment = (index: number) => {
      return commentMatches.some(comment => index >= comment.start && index < comment.end);
    };

    // Highlight strings (single quotes) - but not in comments
    highlighted = highlighted.replace(
      /'([^']*)'/g,
      (match, p1, offset) => {
        if (isInComment(offset)) return match;
        return `<span class="text-green-400">'${p1}'</span>`;
      }
    );

    // Highlight strings (double quotes for identifiers) - but not in comments
    highlighted = highlighted.replace(
      /"([^"]*)"/g,
      (match, p1, offset) => {
        if (isInComment(offset)) return match;
        return `<span class="text-green-400">"${p1}"</span>`;
      }
    );

    // Highlight parameters ({{param}}) - but not in comments
    highlighted = highlighted.replace(
      /\{\{([^}]+)\}\}/g,
      (match, p1, offset) => {
        if (isInComment(offset)) return match;
        return `<span class="text-yellow-400 font-bold">{{${p1}}}</span>`;
      }
    );

    // Highlight keywords (case-insensitive) - but not in comments
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b`, 'gi');
      highlighted = highlighted.replace(
        regex,
        (match, _p1, offset) => {
          if (isInComment(offset)) return match;
          return `<span class="text-blue-400 font-semibold">${match}</span>`;
        }
      );
    });

    // Highlight functions - but not in comments
    functions.forEach(func => {
      const regex = new RegExp(`\\b(${func})\\b`, 'gi');
      highlighted = highlighted.replace(
        regex,
        (match, _p1, offset) => {
          if (isInComment(offset)) return match;
          return `<span class="text-cyan-400">${match}</span>`;
        }
      );
    });

    // Highlight numbers - but not in comments
    highlighted = highlighted.replace(
      /\b(\d+\.?\d*)\b/g,
      (match, _p1, offset) => {
        if (isInComment(offset)) return match;
        return `<span class="text-purple-400">${match}</span>`;
      }
    );

    // Now highlight comments last (so they override everything inside them)
    highlighted = highlighted.replace(
      /--.*$/gm,
      '<span class="text-gray-500">$&</span>'
    );

    return highlighted;
  };

  // Check if the SQL already contains HTML (shouldn't happen, but defensive)
  const containsHTML = sql && (sql.includes('&lt;') || sql.includes('&gt;') || sql.includes('<span'));
  
  if (containsHTML) {
    console.warn('SQLHighlight received SQL that appears to contain HTML:', sql.substring(0, 100));
    // Try to strip HTML tags and entities
    const cleanSQL = sql
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/&lt;/g, '<')    // Unescape HTML entities
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");
    
    return (
      <pre className={`bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-xs ${className}`}>
        <code dangerouslySetInnerHTML={{ __html: highlightSQL(cleanSQL) }} />
      </pre>
    );
  }
  
  return (
    <pre className={`bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-xs ${className}`}>
      <code dangerouslySetInnerHTML={{ __html: highlightSQL(sql) }} />
    </pre>
  );
}