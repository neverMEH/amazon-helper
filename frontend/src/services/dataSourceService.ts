/**
 * Data Source Service
 * API client for AMC schema documentation
 */

import api from './api';
import type {
  DataSource,
  SchemaField,
  QueryExample,
  SchemaSection,
  SchemaRelationship,
  CompleteSchema,
  DataSourceFilters,
  FieldSearchResult,
  TagWithCount,
  AIExport
} from '../types/dataSource';

class DataSourceService {
  /**
   * List data sources with optional filtering
   */
  async listDataSources(filters?: DataSourceFilters): Promise<DataSource[]> {
    const params = new URLSearchParams();
    
    if (filters?.category) params.append('category', filters.category);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.tags) {
      filters.tags.forEach(tag => params.append('tags', tag));
    }
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.offset) params.append('offset', filters.offset.toString());
    
    const response = await api.get(`/data-sources?${params.toString()}`);
    return response.data;
  }

  /**
   * Get a single data source by schema ID
   */
  async getDataSource(schemaId: string): Promise<DataSource> {
    const response = await api.get(`/data-sources/${schemaId}`);
    return response.data;
  }

  /**
   * Get complete schema with all related data
   */
  async getCompleteSchema(schemaId: string): Promise<CompleteSchema> {
    const response = await api.get(`/data-sources/${schemaId}/complete`);
    return response.data;
  }

  /**
   * Get schema fields
   */
  async getSchemaFields(
    schemaId: string,
    dimensionOrMetric?: 'Dimension' | 'Metric',
    aggregationThreshold?: string
  ): Promise<SchemaField[]> {
    const params = new URLSearchParams();
    
    if (dimensionOrMetric) params.append('dimension_or_metric', dimensionOrMetric);
    if (aggregationThreshold) params.append('aggregation_threshold', aggregationThreshold);
    
    const response = await api.get(`/data-sources/${schemaId}/fields?${params.toString()}`);
    return response.data;
  }

  /**
   * Get query examples for a schema
   */
  async getQueryExamples(schemaId: string, category?: string): Promise<QueryExample[]> {
    const params = category ? `?category=${category}` : '';
    const response = await api.get(`/data-sources/${schemaId}/examples${params}`);
    return response.data;
  }

  /**
   * Get documentation sections for a schema
   */
  async getSchemaSections(schemaId: string): Promise<SchemaSection[]> {
    const response = await api.get(`/data-sources/${schemaId}/sections`);
    return response.data;
  }

  /**
   * Get schema relationships
   */
  async getSchemaRelationships(schemaId: string): Promise<{
    from: SchemaRelationship[];
    to: SchemaRelationship[];
  }> {
    const response = await api.get(`/data-sources/${schemaId}/relationships`);
    return response.data;
  }

  /**
   * Get all categories
   */
  async getCategories(): Promise<string[]> {
    const response = await api.get('/data-sources/categories');
    return response.data;
  }

  /**
   * Get popular tags with counts
   */
  async getPopularTags(limit: number = 20): Promise<TagWithCount[]> {
    const response = await api.get(`/data-sources/tags?limit=${limit}`);
    return response.data;
  }

  /**
   * Search fields across all schemas
   */
  async searchFields(query: string, limit: number = 50): Promise<FieldSearchResult[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString()
    });
    
    const response = await api.get(`/data-sources/search-fields?${params.toString()}`);
    return response.data;
  }

  /**
   * Export schemas for AI consumption
   */
  async exportForAI(): Promise<AIExport> {
    const response = await api.get('/data-sources/export-ai');
    return response.data;
  }

  /**
   * Format SQL query for display
   */
  formatSQL(sql: string): string {
    // Basic SQL formatting
    return sql
      .replace(/\bSELECT\b/gi, 'SELECT')
      .replace(/\bFROM\b/gi, '\nFROM')
      .replace(/\bWHERE\b/gi, '\nWHERE')
      .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
      .replace(/\bORDER BY\b/gi, '\nORDER BY')
      .replace(/\bHAVING\b/gi, '\nHAVING')
      .replace(/\bLIMIT\b/gi, '\nLIMIT')
      .replace(/\bJOIN\b/gi, '\nJOIN')
      .replace(/\bLEFT JOIN\b/gi, '\nLEFT JOIN')
      .replace(/\bRIGHT JOIN\b/gi, '\nRIGHT JOIN')
      .replace(/\bINNER JOIN\b/gi, '\nINNER JOIN')
      .replace(/\bUNION\b/gi, '\nUNION')
      .trim();
  }

  /**
   * Get aggregation threshold color
   */
  getThresholdColor(threshold: string): string {
    const colors: Record<string, string> = {
      'NONE': 'text-green-600 bg-green-50',
      'LOW': 'text-blue-600 bg-blue-50',
      'MEDIUM': 'text-yellow-600 bg-yellow-50',
      'HIGH': 'text-orange-600 bg-orange-50',
      'VERY_HIGH': 'text-red-600 bg-red-50',
      'INTERNAL': 'text-gray-600 bg-gray-50'
    };
    return colors[threshold] || 'text-gray-600 bg-gray-50';
  }

  /**
   * Get data type icon
   */
  getDataTypeIcon(dataType: string): string {
    const upperType = dataType.toUpperCase();
    if (upperType.includes('STRING')) return 'Type';
    if (upperType.includes('LONG') || upperType.includes('INTEGER')) return 'Hash';
    if (upperType.includes('DECIMAL') || upperType.includes('FLOAT')) return 'Calculator';
    if (upperType.includes('BOOLEAN')) return 'ToggleLeft';
    if (upperType.includes('DATE') || upperType.includes('TIMESTAMP')) return 'Calendar';
    if (upperType.includes('ARRAY')) return 'List';
    return 'FileText';
  }
}

export const dataSourceService = new DataSourceService();