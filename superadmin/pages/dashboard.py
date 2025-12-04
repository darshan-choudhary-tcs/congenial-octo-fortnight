"""
Dashboard Page for Streamlit Admin Application
Displays system statistics and metrics
"""
import streamlit as st
from utils.api_client import api_client
from utils.db_utils import db_client
from datetime import datetime
import pandas as pd


def format_number(num):
    """Format large numbers with K/M/B suffix"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    return str(num)


def format_bytes(bytes_size):
    """Format bytes to human-readable format"""
    if bytes_size is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def show_dashboard_page():
    """Display dashboard page"""
    st.title("📊 System Dashboard")
    st.markdown("Real-time system statistics and metrics")
    st.markdown("---")

    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    # Check database connection
    if not db_client.check_database_connection():
        st.error("⚠️ Cannot connect to database. Please check backend/data/data_store.db exists.")
        return

    # Fetch data from API and database
    with st.spinner("Loading dashboard data..."):
        # API data (requires admin role)
        system_stats = None
        overall_usage = None

        if st.session_state.get('is_admin', False):
            system_stats = api_client.get_system_stats()
            overall_usage = api_client.get_overall_usage()

        # Database queries (direct access)
        user_stats = db_client.get_user_statistics()
        doc_stats = db_client.get_document_statistics()
        conv_stats = db_client.get_conversation_statistics()
        token_summary = db_client.get_token_usage_summary(days=30)
        agent_stats = db_client.get_agent_statistics()

    # === System Overview ===
    st.subheader("📈 System Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="👥 Total Users",
            value=user_stats.get('total_users', 0),
            delta=f"{user_stats.get('active_users', 0)} active"
        )

    with col2:
        st.metric(
            label="📄 Documents",
            value=doc_stats.get('total_documents', 0),
            delta=f"{doc_stats.get('global_documents', 0)} global"
        )

    with col3:
        st.metric(
            label="💬 Conversations",
            value=conv_stats.get('total_conversations', 0),
            delta=f"{conv_stats.get('total_messages', 0)} messages"
        )

    with col4:
        st.metric(
            label="🤖 Agent Executions",
            value=agent_stats.get('total_executions', 0),
            delta=f"{agent_stats.get('successful', 0)} successful"
        )

    st.markdown("---")

    # === Token Usage Overview ===
    st.subheader("💰 Token Usage (Last 30 Days)")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Tokens",
            value=format_number(token_summary.get('total_tokens', 0))
        )

    with col2:
        st.metric(
            label="Total Cost",
            value=f"${token_summary.get('total_cost', 0):.2f}"
        )

    with col3:
        st.metric(
            label="Operations",
            value=format_number(token_summary.get('total_operations', 0))
        )

    with col4:
        st.metric(
            label="Active Users",
            value=token_summary.get('unique_users', 0)
        )

    st.markdown("---")

    # === Two Column Layout ===
    col1, col2 = st.columns(2)

    with col1:
        # Document Statistics
        st.subheader("📚 Document Statistics")

        doc_by_type = db_client.get_documents_by_type()
        if doc_by_type:
            df = pd.DataFrame(doc_by_type)
            df['total_size_mb'] = df['total_size'] / (1024 * 1024)

            st.dataframe(
                df[['file_type', 'count', 'total_size_mb']].rename(columns={
                    'file_type': 'Type',
                    'count': 'Count',
                    'total_size_mb': 'Size (MB)'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No documents found")

        # Processing Status
        pending = doc_stats.get('pending_documents', 0)
        failed = doc_stats.get('failed_documents', 0)
        processed = doc_stats.get('processed_documents', 0)

        if pending > 0 or failed > 0:
            st.warning(f"⚠️ {pending} pending, {failed} failed documents")
        else:
            st.success(f"✅ All {processed} documents processed")

        st.markdown("---")

        # Token Usage by Provider
        st.subheader("🔌 Usage by Provider")

        provider_usage = db_client.get_token_usage_by_provider(days=30)
        if provider_usage:
            df = pd.DataFrame(provider_usage)
            st.dataframe(
                df[['provider', 'model', 'total_tokens', 'total_cost']].rename(columns={
                    'provider': 'Provider',
                    'model': 'Model',
                    'total_tokens': 'Tokens',
                    'total_cost': 'Cost ($)'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No usage data")

    with col2:
        # Conversation Statistics
        st.subheader("💬 Conversation Analytics")

        conv_by_provider = db_client.get_conversations_by_provider()
        if conv_by_provider:
            df = pd.DataFrame(conv_by_provider)
            st.dataframe(
                df.rename(columns={
                    'llm_provider': 'Provider',
                    'llm_model': 'Model',
                    'conversation_count': 'Conversations'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No conversations found")

        # Average confidence score
        avg_confidence = conv_stats.get('avg_confidence')
        if avg_confidence:
            confidence_pct = avg_confidence * 100
            st.metric("Average Confidence Score", f"{confidence_pct:.1f}%")

        st.markdown("---")

        # Agent Performance
        st.subheader("🤖 Agent Performance")

        agent_perf = db_client.get_agent_performance()
        if agent_perf:
            df = pd.DataFrame(agent_perf)
            # Show top 5 agents
            df_top = df.head(5)
            st.dataframe(
                df_top[['agent_name', 'executions', 'successful', 'avg_execution_time']].rename(columns={
                    'agent_name': 'Agent',
                    'executions': 'Runs',
                    'successful': 'Success',
                    'avg_execution_time': 'Avg Time (s)'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No agent execution data")

    st.markdown("---")

    # === Recent Activity ===
    st.subheader("📋 Recent Activity")

    tab1, tab2, tab3 = st.tabs(["Documents", "Agent Logs", "Token Usage"])

    with tab1:
        recent_docs = db_client.get_recent_documents(limit=10)
        if recent_docs:
            df = pd.DataFrame(recent_docs)
            df['uploaded_at'] = pd.to_datetime(df['uploaded_at']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(
                df[['filename', 'file_type', 'scope', 'processing_status', 'uploaded_by', 'uploaded_at']].rename(columns={
                    'filename': 'Filename',
                    'file_type': 'Type',
                    'scope': 'Scope',
                    'processing_status': 'Status',
                    'uploaded_by': 'Uploaded By',
                    'uploaded_at': 'Date'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent documents")

    with tab2:
        recent_logs = db_client.get_recent_agent_logs(limit=20)
        if recent_logs:
            df = pd.DataFrame(recent_logs)
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(
                df[['agent_name', 'agent_type', 'action', 'status', 'execution_time', 'created_at']].rename(columns={
                    'agent_name': 'Agent',
                    'agent_type': 'Type',
                    'action': 'Action',
                    'status': 'Status',
                    'execution_time': 'Time (s)',
                    'created_at': 'Timestamp'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent agent logs")

    with tab3:
        top_users = db_client.get_top_users_by_usage(limit=10, days=30)
        if top_users:
            df = pd.DataFrame(top_users)
            st.dataframe(
                df[['username', 'total_tokens', 'total_cost', 'conversations']].rename(columns={
                    'username': 'User',
                    'total_tokens': 'Tokens',
                    'total_cost': 'Cost ($)',
                    'conversations': 'Conversations'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No usage data")

    # === System Health ===
    st.markdown("---")
    st.subheader("🏥 System Health")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        db_size = db_client.get_database_size()
        st.metric("Database Size", format_bytes(db_size))

    with col2:
        success_rate = 0
        if agent_stats.get('total_executions', 0) > 0:
            success_rate = (agent_stats.get('successful', 0) / agent_stats.get('total_executions', 1)) * 100
        st.metric("Agent Success Rate", f"{success_rate:.1f}%")

    with col3:
        avg_exec_time = agent_stats.get('avg_execution_time', 0)
        st.metric("Avg Agent Time", f"{avg_exec_time:.2f}s" if avg_exec_time else "N/A")

    with col4:
        total_chunks = doc_stats.get('total_chunks', 0)
        st.metric("Total Chunks", format_number(total_chunks))


if __name__ == "__main__":
    show_dashboard_page()
