"""
Database Utilities for Streamlit Application
Direct SQLite database access for analytics and queries
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import streamlit as st
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_PATH = "../backend/data/data_store.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class DatabaseClient:
    """Client for direct database access"""

    def __init__(self):
        self.engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def get_session(self):
        """Get database session with context manager"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results as dict"""
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            st.error(f"Database query failed: {str(e)}")
            return []

    # User statistics
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        query = """
        SELECT
            COUNT(*) as total_users,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users,
            SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive_users
        FROM users
        """
        result = self.execute_query(query)
        return result[0] if result else {"total_users": 0, "active_users": 0, "inactive_users": 0}

    def get_users_by_role(self) -> List[Dict[str, Any]]:
        """Get user count by role"""
        query = """
        SELECT
            r.name as role_name,
            COUNT(DISTINCT u.id) as user_count
        FROM roles r
        LEFT JOIN user_roles ur ON r.id = ur.role_id
        LEFT JOIN users u ON ur.user_id = u.id
        GROUP BY r.id, r.name
        ORDER BY user_count DESC
        """
        return self.execute_query(query)

    # Document statistics
    def get_document_statistics(self) -> Dict[str, Any]:
        """Get document statistics"""
        query = """
        SELECT
            COUNT(*) as total_documents,
            SUM(CASE WHEN scope = 'global' THEN 1 ELSE 0 END) as global_documents,
            SUM(CASE WHEN scope = 'user' THEN 1 ELSE 0 END) as user_documents,
            SUM(CASE WHEN is_processed = 1 THEN 1 ELSE 0 END) as processed_documents,
            SUM(CASE WHEN processing_status = 'pending' THEN 1 ELSE 0 END) as pending_documents,
            SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) as failed_documents,
            SUM(num_chunks) as total_chunks,
            SUM(file_size) as total_size_bytes
        FROM documents
        """
        result = self.execute_query(query)
        return result[0] if result else {}

    def get_documents_by_type(self) -> List[Dict[str, Any]]:
        """Get document count by file type"""
        query = """
        SELECT
            file_type,
            COUNT(*) as count,
            SUM(file_size) as total_size
        FROM documents
        GROUP BY file_type
        ORDER BY count DESC
        """
        return self.execute_query(query)

    def get_recent_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently uploaded documents"""
        query = """
        SELECT
            d.uuid,
            d.filename,
            d.file_type,
            d.title,
            d.scope,
            d.processing_status,
            d.uploaded_at,
            u.username as uploaded_by
        FROM documents d
        LEFT JOIN users u ON d.uploaded_by_id = u.id
        ORDER BY d.uploaded_at DESC
        LIMIT :limit
        """
        return self.execute_query(query, {"limit": limit})

    # Conversation statistics
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        query = """
        SELECT
            COUNT(DISTINCT c.id) as total_conversations,
            COUNT(DISTINCT c.user_id) as active_users,
            COUNT(m.id) as total_messages,
            AVG(CASE WHEN m.role = 'assistant' THEN m.confidence_score END) as avg_confidence
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        """
        result = self.execute_query(query)
        return result[0] if result else {}

    def get_conversations_by_provider(self) -> List[Dict[str, Any]]:
        """Get conversation count by LLM provider"""
        query = """
        SELECT
            llm_provider,
            llm_model,
            COUNT(*) as conversation_count
        FROM conversations
        GROUP BY llm_provider, llm_model
        ORDER BY conversation_count DESC
        """
        return self.execute_query(query)

    # Token usage analytics
    def get_token_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get token usage summary for last N days"""
        query = """
        SELECT
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(embedding_tokens) as total_embedding_tokens,
            SUM(estimated_cost) as total_cost,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(*) as total_operations
        FROM token_usage
        WHERE created_at >= datetime('now', '-' || :days || ' days')
        """
        result = self.execute_query(query, {"days": days})
        return result[0] if result else {}

    def get_token_usage_by_provider(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get token usage breakdown by provider"""
        query = """
        SELECT
            provider,
            model,
            SUM(total_tokens) as total_tokens,
            SUM(estimated_cost) as total_cost,
            COUNT(*) as operations
        FROM token_usage
        WHERE created_at >= datetime('now', '-' || :days || ' days')
        GROUP BY provider, model
        ORDER BY total_tokens DESC
        """
        return self.execute_query(query, {"days": days})

    def get_token_usage_by_operation(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get token usage by operation type"""
        query = """
        SELECT
            operation_type,
            SUM(total_tokens) as total_tokens,
            SUM(estimated_cost) as total_cost,
            COUNT(*) as operations
        FROM token_usage
        WHERE created_at >= datetime('now', '-' || :days || ' days')
        GROUP BY operation_type
        ORDER BY total_tokens DESC
        """
        return self.execute_query(query, {"days": days})

    def get_daily_token_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily token usage trend"""
        query = """
        SELECT
            DATE(created_at) as date,
            SUM(total_tokens) as total_tokens,
            SUM(estimated_cost) as total_cost,
            COUNT(*) as operations
        FROM token_usage
        WHERE created_at >= datetime('now', '-' || :days || ' days')
        GROUP BY DATE(created_at)
        ORDER BY date ASC
        """
        return self.execute_query(query, {"days": days})

    def get_top_users_by_usage(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """Get top users by token usage"""
        query = """
        SELECT
            u.username,
            u.email,
            SUM(tu.total_tokens) as total_tokens,
            SUM(tu.estimated_cost) as total_cost,
            COUNT(DISTINCT tu.conversation_id) as conversations
        FROM token_usage tu
        JOIN users u ON tu.user_id = u.id
        WHERE tu.created_at >= datetime('now', '-' || :days || ' days')
        GROUP BY u.id, u.username, u.email
        ORDER BY total_tokens DESC
        LIMIT :limit
        """
        return self.execute_query(query, {"limit": limit, "days": days})

    # Agent statistics
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get agent execution statistics"""
        query = """
        SELECT
            COUNT(*) as total_executions,
            COUNT(DISTINCT agent_name) as unique_agents,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            AVG(execution_time) as avg_execution_time,
            SUM(tokens_used) as total_tokens
        FROM agent_logs
        """
        result = self.execute_query(query)
        return result[0] if result else {}

    def get_agent_performance(self) -> List[Dict[str, Any]]:
        """Get performance metrics by agent"""
        query = """
        SELECT
            agent_name,
            agent_type,
            COUNT(*) as executions,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
            AVG(execution_time) as avg_execution_time,
            AVG(confidence) as avg_confidence,
            SUM(tokens_used) as total_tokens
        FROM agent_logs
        GROUP BY agent_name, agent_type
        ORDER BY executions DESC
        """
        return self.execute_query(query)

    def get_recent_agent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent agent execution logs"""
        query = """
        SELECT
            al.agent_name,
            al.agent_type,
            al.action,
            al.status,
            al.execution_time,
            al.confidence,
            al.created_at,
            m.content as message_content
        FROM agent_logs al
        LEFT JOIN messages m ON al.message_id = m.id
        ORDER BY al.created_at DESC
        LIMIT :limit
        """
        return self.execute_query(query, {"limit": limit})

    # System health checks
    def check_database_connection(self) -> bool:
        """Check if database is accessible"""
        try:
            query = "SELECT 1"
            result = self.execute_query(query)
            return len(result) > 0
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False

    def get_database_size(self) -> Optional[int]:
        """Get database file size in bytes"""
        try:
            import os
            if os.path.exists(DATABASE_PATH):
                return os.path.getsize(DATABASE_PATH)
            return None
        except Exception as e:
            logger.error(f"Failed to get database size: {str(e)}")
            return None


# Singleton instance
db_client = DatabaseClient()
