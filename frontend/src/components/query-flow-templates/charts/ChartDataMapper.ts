import type { TemplateChartConfig, ChartDataMapping } from '../../../types/queryFlowTemplate';

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string;
    borderWidth?: number;
    fill?: boolean;
    type?: string; // For combo charts
  }[];
}

export interface TableData {
  columns: {
    field: string;
    header: string;
    format?: string;
    width?: number;
  }[];
  rows: Record<string, any>[];
  totalCount: number;
}

export class ChartDataMapper {
  
  static mapToChartData(
    rawData: any[],
    chartConfig: TemplateChartConfig
  ): ChartData | TableData {
    if (!rawData || rawData.length === 0) {
      return { labels: [], datasets: [] };
    }

    const { chart_type } = chartConfig;

    if (chart_type === 'table') {
      return this.mapToTableData(rawData, chartConfig);
    }

    return this.mapToVisualizationData(rawData, chartConfig);
  }

  private static mapToTableData(
    rawData: any[],
    chartConfig: TemplateChartConfig
  ): TableData {
    const columns = chartConfig.chart_config.columns || 
      Object.keys(rawData[0] || {}).map(key => ({
        field: key,
        header: this.formatColumnHeader(key),
        format: this.detectFormat(rawData, key)
      }));

    const rows = rawData.map(row => {
      const formattedRow: Record<string, any> = {};
      columns.forEach(col => {
        const value = row[col.field];
        formattedRow[col.field] = this.formatCellValue(value, col.format);
      });
      return formattedRow;
    });

    return {
      columns,
      rows,
      totalCount: rows.length
    };
  }

  private static mapToVisualizationData(
    rawData: any[],
    chartConfig: TemplateChartConfig
  ): ChartData {
    const { data_mapping, chart_type } = chartConfig;
    
    // Sort data if specified
    let sortedData = [...rawData];
    if (data_mapping.sort_by) {
      sortedData.sort((a, b) => {
        const aVal = a[data_mapping.sort_by!];
        const bVal = b[data_mapping.sort_by!];
        const comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
        return data_mapping.sort_order === 'desc' ? -comparison : comparison;
      });
    }

    // Limit data if specified
    if (data_mapping.limit) {
      sortedData = sortedData.slice(0, data_mapping.limit);
    }

    switch (chart_type) {
      case 'pie':
        return this.mapToPieData(sortedData, data_mapping);
      case 'line':
      case 'area':
        return this.mapToTimeSeriesData(sortedData, data_mapping, chart_type);
      case 'bar':
        return this.mapToBarData(sortedData, data_mapping);
      case 'scatter':
        return this.mapToScatterData(sortedData, data_mapping);
      case 'combo':
        return this.mapToComboData(sortedData, data_mapping);
      default:
        return this.mapToDefaultData(sortedData, data_mapping);
    }
  }

  private static mapToPieData(data: any[], mapping: ChartDataMapping): ChartData {
    const labels = data.map(row => 
      this.formatValue(row[mapping.x_field!], mapping.value_format)
    );
    const values = data.map(row => 
      this.aggregateValue(row[mapping.y_field!], mapping.aggregation || undefined)
    );

    return {
      labels,
      datasets: [{
        label: mapping.y_field || 'Value',
        data: values,
        backgroundColor: this.generateColors(data.length, mapping.color_scheme)
      }]
    };
  }

  private static mapToTimeSeriesData(
    data: any[], 
    mapping: ChartDataMapping, 
    chartType: 'line' | 'area'
  ): ChartData {
    const labels = data.map(row => 
      this.formatValue(row[mapping.x_field!], 'date')
    );

    const datasets: any[] = [];

    if (mapping.y_fields && mapping.y_fields.length > 1) {
      // Multiple series
      mapping.y_fields.forEach((field, index) => {
        datasets.push({
          label: this.formatColumnHeader(field),
          data: data.map(row => this.aggregateValue(row[field], mapping.aggregation || undefined)),
          borderColor: this.generateColors(1, mapping.color_scheme, index)[0],
          backgroundColor: chartType === 'area' 
            ? this.generateColors(1, mapping.color_scheme, index, 0.3)[0]
            : undefined,
          fill: chartType === 'area',
          borderWidth: 2
        });
      });
    } else {
      // Single series
      const field = mapping.y_field || mapping.y_fields?.[0];
      if (field) {
        datasets.push({
          label: this.formatColumnHeader(field),
          data: data.map(row => this.aggregateValue(row[field], mapping.aggregation || undefined)),
          borderColor: this.generateColors(1, mapping.color_scheme)[0],
          backgroundColor: chartType === 'area' 
            ? this.generateColors(1, mapping.color_scheme, 0, 0.3)[0]
            : undefined,
          fill: chartType === 'area',
          borderWidth: 2
        });
      }
    }

    return { labels, datasets };
  }

  private static mapToBarData(data: any[], mapping: ChartDataMapping): ChartData {
    const labels = data.map(row => 
      this.formatValue(row[mapping.x_field!], mapping.value_format)
    );

    const datasets: any[] = [];
    const fields = mapping.y_fields || [mapping.y_field!];

    fields.forEach((field, index) => {
      if (field) {
        datasets.push({
          label: this.formatColumnHeader(field),
          data: data.map(row => this.aggregateValue(row[field], mapping.aggregation || undefined)),
          backgroundColor: this.generateColors(fields.length, mapping.color_scheme, index)[0],
          borderWidth: 1
        });
      }
    });

    return { labels, datasets };
  }

  private static mapToScatterData(data: any[], mapping: ChartDataMapping): ChartData {
    const scatterData = data.map(row => ({
      x: row[mapping.x_field!],
      y: row[mapping.y_field!]
    }));

    return {
      labels: [],
      datasets: [{
        label: `${mapping.x_field} vs ${mapping.y_field}`,
        data: scatterData as any,
        backgroundColor: this.generateColors(1, mapping.color_scheme)[0]
      }]
    };
  }

  private static mapToComboData(data: any[], mapping: ChartDataMapping): ChartData {
    const labels = data.map(row => 
      this.formatValue(row[mapping.x_field!], mapping.value_format)
    );

    const datasets: any[] = [];
    const fields = mapping.y_fields || [mapping.y_field!];

    fields.forEach((field, index) => {
      if (field) {
        datasets.push({
          label: this.formatColumnHeader(field),
          data: data.map(row => this.aggregateValue(row[field], mapping.aggregation || undefined)),
          backgroundColor: this.generateColors(fields.length, mapping.color_scheme, index)[0],
          borderColor: this.generateColors(fields.length, mapping.color_scheme, index)[0],
          type: index === 0 ? 'bar' : 'line', // First dataset as bar, rest as line
          borderWidth: 2
        });
      }
    });

    return { labels, datasets };
  }

  private static mapToDefaultData(data: any[], mapping: ChartDataMapping): ChartData {
    return this.mapToBarData(data, mapping);
  }

  // Utility methods

  private static formatColumnHeader(field: string): string {
    return field
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  private static formatValue(value: any, format?: string): string {
    if (value == null) return '';

    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', { 
          style: 'currency', 
          currency: 'USD' 
        }).format(Number(value));
      case 'percentage':
        return `${(Number(value) * 100).toFixed(2)}%`;
      case 'number':
        return Number(value).toLocaleString();
      case 'date':
        return new Date(value).toLocaleDateString();
      default:
        return String(value);
    }
  }

  private static formatCellValue(value: any, format?: string): any {
    if (value == null) return '';
    
    // Keep raw value for table sorting/filtering, but store formatted display value
    return {
      raw: value,
      display: this.formatValue(value, format)
    };
  }

  private static aggregateValue(value: any, aggregation?: string): number {
    const num = Number(value);
    
    switch (aggregation) {
      case 'sum':
      case 'avg':
      case 'count':
      case 'min':
      case 'max':
        // These would be pre-aggregated from SQL query
        return num;
      default:
        return num;
    }
  }

  private static detectFormat(data: any[], field: string): string {
    if (!data.length) return 'string';
    
    const sampleValue = data[0][field];
    
    if (typeof sampleValue === 'number') {
      if (field.toLowerCase().includes('rate') || 
          field.toLowerCase().includes('percent')) {
        return 'percentage';
      }
      if (field.toLowerCase().includes('cost') || 
          field.toLowerCase().includes('spend') ||
          field.toLowerCase().includes('revenue')) {
        return 'currency';
      }
      return 'number';
    }
    
    if (Date.parse(sampleValue)) {
      return 'date';
    }
    
    return 'string';
  }

  private static generateColors(
    count: number, 
    scheme?: string, 
    index: number = 0,
    alpha: number = 1
  ): string[] {
    const colorSchemes = {
      blue: ['#3B82F6', '#1E40AF', '#1E3A8A', '#172554'],
      green: ['#10B981', '#059669', '#047857', '#064E3B'],
      purple: ['#8B5CF6', '#7C3AED', '#6D28D9', '#5B21B6'],
      red: ['#EF4444', '#DC2626', '#B91C1C', '#991B1B'],
      mixed: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
    };

    const colors = colorSchemes[scheme as keyof typeof colorSchemes] || colorSchemes.mixed;
    const result: string[] = [];

    for (let i = 0; i < count; i++) {
      const colorIndex = (index + i) % colors.length;
      const color = colors[colorIndex];
      
      if (alpha < 1) {
        // Convert hex to rgba
        const hex = color.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        result.push(`rgba(${r}, ${g}, ${b}, ${alpha})`);
      } else {
        result.push(color);
      }
    }

    return result;
  }
}

export default ChartDataMapper;