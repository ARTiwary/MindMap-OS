export type NodeType =
  | "IDEA" | "NOTE" | "CONCEPT" | "QUESTION" | "RESOURCE"
  | "PROJECT" | "BOOK" | "COURSE" | "PERSON" | "TOPIC" | "REFERENCE";

export type NodeStatus = "DRAFT" | "ACTIVE" | "ARCHIVED" | "COMPLETED";
export type Importance = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type RelationshipType =
  | "RELATED_TO" | "PARENT_OF" | "CHILD_OF" | "REQUIRES" | "DEPENDS_ON"
  | "INSPIRES" | "REFERENCES" | "DERIVED_FROM" | "PART_OF" | "CONTRADICTS" | "SUPPORTS";

export interface Tag {
  id: string;
  name: string;
  color: string;
}

export interface KnowledgeNode {
  id: string;
  user_id: string;
  title: string;
  slug: string;
  description?: string | null;
  content?: string | null;
  node_type: NodeType;
  status: NodeStatus;
  importance: Importance;
  color?: string | null;
  icon?: string | null;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
  last_accessed_at?: string | null;
  tags: Tag[];
}

export interface NodeDetail extends KnowledgeNode {
  referenced_by_count: number;
  references_count: number;
}

export interface PaginatedNodes {
  items: KnowledgeNode[];
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface Relationship {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: RelationshipType;
  label?: string | null;
  strength: number;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  is_verified: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface DashboardStats {
  total_nodes: number;
  total_connections: number;
  total_tags: number;
  total_projects: number;
  total_favorites: number;
  knowledge_density: number;
  growth: { date: string; count: number }[];
  recently_updated: { id: string; title: string; node_type: NodeType; slug: string }[];
  favorites: { id: string; title: string; node_type: NodeType; slug: string }[];
  recently_viewed_ids: string[];
  popular_node_ids: { node_id: string; views: number }[];
}
