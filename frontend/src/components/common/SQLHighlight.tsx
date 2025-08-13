interface SQLHighlightProps {
  sql: string;
  className?: string;
}

export default function SQLHighlight({ sql, className = '' }: SQLHighlightProps) {
  // Pre-clean the SQL before processing to handle any embedded artifacts
  const preCleanSQL = (input: string): string => {
    if (!input) return '';
    
    // Aggressively remove all HTML-like artifacts before processing
    return input
      // Remove specific patterns we're seeing in the data
      .replace(/\b\d+\s*font-[^">]*">/g, '') // "400 font-semibold">
      .replace(/\b\d+">"[^"]*"/g, '') // 400">"text-green-400"
      .replace(/"text-[^"]*"/g, '') // "text-green-400"
      .replace(/\b\d+">'/g, "'") // 400">' -> just '
      .replace(/"\s*>/g, '') // "> artifacts
      // Clean up the results
      .replace(/\s{2,}/g, ' ') // Multiple spaces to single
      .replace(/>\s*'/g, "'") // >' -> '
      .trim();
  };
  
  // SQL keywords for highlighting
  const keywords = [
    'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON',
    'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'WITH', 'UNION',
    'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CREATE', 'TABLE',
    'ALTER', 'DROP', 'INDEX', 'VIEW', 'TRIGGER', 'PROCEDURE', 'FUNCTION',
    'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AND', 'OR', 'NOT', 'IN', 'EXISTS',
    'BETWEEN', 'LIKE', 'IS', 'NULL', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN',
    'MAX', 'CAST', 'CONVERT', 'COALESCE', 'NULLIF', 'PARTITION', 'OVER',
    'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'LAG', 'LEAD', 'FIRST_VALUE', 'LAST_VALUE',
    'ALL', 'ARRAY_SORT', 'COLLECT'
  ];

  const functions = [
    'DATE', 'DATETIME', 'TIMESTAMP', 'EXTRACT', 'DATE_ADD', 'DATE_SUB', 'DATEDIFF',
    'SUBSTRING', 'CONCAT', 'LENGTH', 'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM',
    'REPLACE', 'ROUND', 'FLOOR', 'CEILING', 'ABS', 'MOD', 'POWER', 'SQRT'
  ];

  const highlightSQL = (query: string) => {
    // First decode any HTML entities that might be in the input
    let cleanQuery = query
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ');
    
    // Remove any HTML tags and artifacts - more aggressive cleaning
    cleanQuery = cleanQuery
      .replace(/<[^>]*>/g, '') // Remove all HTML tags
      // Remove specific artifacts we're seeing
      .replace(/\d+\s*font-semibold">/g, '') // Remove "400 font-semibold">
      .replace(/\d+">"/g, '') // Remove '400">"'
      .replace(/text-[a-z-]+\d*">/g, '') // Remove text-color classes like "text-green-400">
      .replace(/"text-[a-z-]+\d*">/g, '') // Remove quoted text classes
      .replace(/\d+">/g, '') // Remove number artifacts like '400">'
      // More general cleanup patterns
      .replace(/\s+font-[^"]*">/g, '') // Remove font class artifacts
      .replace(/">/g, '') // Remove dangling quotes
      .replace(/class="[^"]*"/g, '') // Remove any class attributes
      .replace(/style="[^"]*"/g, '') // Remove any style attributes
      .replace(/\s{2,}/g, ' ') // Collapse multiple spaces
      .trim();

    // Format the SQL for better readability
    // Add newlines after major SQL keywords
    cleanQuery = cleanQuery
      .replace(/\s+(FROM|WHERE|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|GROUP BY|ORDER BY|HAVING|LIMIT|UNION|WITH)\s+/gi, '\n$1 ')
      .replace(/\s+(AND|OR)\s+/gi, '\n  $1 ')
      .replace(/,\s*(?=[A-Za-z_])/g, ',\n  ') // Add newlines after commas in SELECT lists
      .trim();

    // Now escape HTML to prevent XSS
    let highlighted = cleanQuery
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

  // Clean up any HTML artifacts that might be in the SQL
  if (!sql) {
    return (
      <pre className={`bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-xs ${className}`}>
        <code className="text-gray-500">-- No SQL query available</code>
      </pre>
    );
  }

  // Always pre-clean and then process the SQL through our formatting logic
  const cleanedSQL = preCleanSQL(sql);
  
  return (
    <pre className={`bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-xs font-mono ${className}`}>
      <code 
        dangerouslySetInnerHTML={{ __html: highlightSQL(cleanedSQL) }} 
        style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
      />
    </pre>
  );
}