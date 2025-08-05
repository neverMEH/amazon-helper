interface Props {
  data: any;
}

export default function ResultsTable({ data }: Props) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="text-sm text-gray-500 p-4 bg-gray-50 rounded-md">
        No results available
      </div>
    );
  }

  // Get column headers from first row
  const columns = Object.keys(data[0]);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-300">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column}
                className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {data.map((row, idx) => (
            <tr key={idx}>
              {columns.map((column) => (
                <td
                  key={column}
                  className="whitespace-nowrap px-3 py-4 text-sm text-gray-500"
                >
                  {row[column]?.toString() || '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}