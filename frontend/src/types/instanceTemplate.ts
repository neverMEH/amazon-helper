/**
 * Instance Template Types
 *
 * Types for SQL templates scoped to specific AMC instances.
 * Instance templates are simpler than query templates - no parameters or sharing.
 */

export interface InstanceTemplate {
  id: string;
  templateId: string;
  name: string;
  description?: string;
  sqlQuery: string;
  instanceId: string;
  userId: string;
  tags: string[];
  usageCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface InstanceTemplateCreate {
  name: string;
  description?: string;
  sql_query: string;
  tags?: string[];
}

export interface InstanceTemplateUpdate {
  name?: string;
  description?: string;
  sql_query?: string;
  tags?: string[];
}

export interface InstanceTemplateResponse {
  templateId: string;
  name: string;
  instanceId: string;
  createdAt: string;
}

export interface InstanceTemplateListItem {
  id: string;
  templateId: string;
  name: string;
  description?: string;
  sqlQuery: string;
  instanceId: string;
  tags: string[];
  usageCount: number;
  createdAt: string;
  updatedAt: string;
}
