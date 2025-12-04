"""
LLM Configuration Page for Streamlit Admin Application
Manage dual LLM providers and RAG settings
"""
import streamlit as st
from utils.api_client import api_client
import json
import os
import subprocess
import time
from pathlib import Path


def update_env_file(updates: dict) -> bool:
    """Update .env file in backend directory"""
    try:
        # Path to backend .env file
        backend_dir = Path(__file__).parent.parent.parent / "backend"
        env_file = backend_dir / ".env"

        # Read existing .env file
        env_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_lines = f.readlines()

        # Update or add environment variables
        updated_keys = set()
        new_lines = []

        for line in env_lines:
            line = line.rstrip()
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0].strip()
                if key in updates:
                    # Update existing key
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line + '\n')
            else:
                new_lines.append(line + '\n')

        # Add new keys that weren't in the file
        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")

        # Write back to .env file
        with open(env_file, 'w') as f:
            f.writelines(new_lines)

        return True
    except Exception as e:
        st.error(f"Failed to update .env file: {str(e)}")
        return False


def restart_backend() -> bool:
    """Restart the backend server"""
    try:
        backend_dir = Path(__file__).parent.parent.parent / "backend"

        # Kill existing backend process
        st.info("🔄 Stopping backend...")
        kill_result = subprocess.run(
            "kill $(lsof -t -i:8000) 2>/dev/null || true",
            shell=True,
            capture_output=True,
            text=True
        )

        # Wait a moment for the process to die
        time.sleep(2)

        # Start new backend process
        st.info("🚀 Starting backend...")
        log_file = backend_dir.parent / "backend.log"

        # Start backend in background
        subprocess.Popen(
            f"cd {backend_dir} && uvicorn main:app --reload --port 8000 > {log_file} 2>&1",
            shell=True,
            start_new_session=True
        )

        # Wait a moment for startup
        time.sleep(3)

        return True
    except Exception as e:
        st.error(f"Failed to restart backend: {str(e)}")
        return False


def show_llm_config_page():
    """Display LLM configuration page"""
    st.title("⚙️ LLM Configuration")
    st.markdown("Manage dual LLM providers and RAG settings")
    st.markdown("---")

    # Check if user is admin
    if not st.session_state.get('is_admin', False):
        st.error("⛔ Access Denied: Admin privileges required")
        st.info("Please login as an admin user to access LLM configuration.")
        return

    # Fetch current configuration
    with st.spinner("Loading configuration..."):
        config = api_client.get_llm_config()

    if not config:
        st.error("Failed to load LLM configuration from backend")
        st.info("Make sure you're logged in as admin and the backend is running.")
        return

    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔌 Custom API Provider",
        "🏠 Ollama Provider",
        "🔍 RAG Configuration",
        "🤖 Agent Settings"
    ])

    # === CUSTOM API PROVIDER ===
    with tab1:
        st.subheader("Custom API Provider (GenAI Lab)")
        st.markdown("Configure external LLM API provider")

        with st.form("custom_provider_form"):
            col1, col2 = st.columns(2)

            with col1:
                custom_base_url = st.text_input(
                    "Base URL",
                    value=config.get('llm', {}).get('custom_base_url', ''),
                    help="API endpoint base URL"
                )

                custom_model = st.text_input(
                    "Chat Model",
                    value=config.get('llm', {}).get('custom_model', ''),
                    help="Model name for chat completions"
                )

                custom_api_key = st.text_input(
                    "API Key",
                    type="password",
                    value=config.get('llm', {}).get('custom_api_key', ''),
                    help="API key (masked in display)"
                )

            with col2:
                custom_embedding_model = st.text_input(
                    "Embedding Model",
                    value=config.get('llm', {}).get('custom_embedding_model', ''),
                    help="Model name for embeddings"
                )

                custom_vision_model = st.text_input(
                    "Vision Model",
                    value=config.get('vision', {}).get('custom_vision_model', ''),
                    help="Model name for vision/OCR tasks"
                )

            st.markdown("**Pricing (per 1M tokens)**")
            col1, col2 = st.columns(2)
            with col1:
                prompt_cost = st.number_input(
                    "Prompt Tokens Cost ($)",
                    value=0.14,
                    step=0.01,
                    format="%.2f"
                )
            with col2:
                completion_cost = st.number_input(
                    "Completion Tokens Cost ($)",
                    value=0.28,
                    step=0.01,
                    format="%.2f"
                )

            submitted = st.form_submit_button("💾 Save Custom Provider Settings", use_container_width=True)

            if submitted:
                with st.spinner("Saving configuration..."):
                    # Prepare environment variable updates
                    env_updates = {
                        'CUSTOM_LLM_BASE_URL': custom_base_url,
                        'CUSTOM_LLM_MODEL': custom_model,
                        'CUSTOM_EMBEDDING_MODEL': custom_embedding_model,
                        'CUSTOM_VISION_MODEL': custom_vision_model,
                    }

                    # Only update API key if it's not the masked version
                    if custom_api_key and not custom_api_key.startswith('***'):
                        env_updates['CUSTOM_LLM_API_KEY'] = custom_api_key

                    # Update .env file
                    if update_env_file(env_updates):
                        st.success("✅ Configuration saved to .env file")

                        # Restart backend
                        st.warning("⚠️ Restarting backend server...")
                        if restart_backend():
                            st.success("✅ Backend restarted successfully!")
                            st.info("🔄 Please wait a few seconds, then refresh this page to see updated values.")
                            st.balloons()
                        else:
                            st.error("❌ Failed to restart backend. Please restart manually.")
                    else:
                        st.error("❌ Failed to save configuration")

        # Backend Logs Section
        st.markdown("---")
        st.subheader("📋 Backend Logs")

        col1, col2 = st.columns([3, 1])
        with col1:
            log_lines = st.slider("Number of log lines to display", min_value=10, max_value=200, value=50, step=10)
        with col2:
            if st.button("🔄 Refresh Logs", use_container_width=True):
                st.rerun()

        try:
            log_file_path = Path(__file__).parent.parent.parent / "backend.log"
            if log_file_path.exists():
                with open(log_file_path, 'r') as f:
                    # Read last N lines
                    lines = f.readlines()
                    last_lines = lines[-log_lines:] if len(lines) > log_lines else lines
                    log_content = ''.join(last_lines)

                st.code(log_content, language="log")
                st.caption(f"Showing last {len(last_lines)} lines from {log_file_path}")
            else:
                st.warning("⚠️ Backend log file not found. Start the backend to generate logs.")
        except Exception as e:
            st.error(f"Failed to read backend logs: {str(e)}")

        # Display current settings
        with st.expander("📋 Current Settings", expanded=False):
            llm_config = {
                "base_url": config.get('llm', {}).get('custom_base_url', ''),
                "model": config.get('llm', {}).get('custom_model', ''),
                "api_key": config.get('llm', {}).get('custom_api_key', ''),
                "embedding_model": config.get('llm', {}).get('custom_embedding_model', ''),
                "vision_model": config.get('vision', {}).get('custom_vision_model', ''),
                "vision_available": config.get('provider_status', {}).get('custom_vision_available', False)
            }
            st.json(llm_config)

    # === OLLAMA PROVIDER ===
    with tab2:
        st.subheader("Ollama Provider (Local)")
        st.markdown("Configure local Ollama instance")

        with st.form("ollama_provider_form"):
            col1, col2 = st.columns(2)

            with col1:
                ollama_base_url = st.text_input(
                    "Base URL",
                    value=config.get('llm', {}).get('ollama_base_url', ''),
                    help="Ollama server URL (typically http://localhost:11434)"
                )

                ollama_model = st.text_input(
                    "Chat Model",
                    value=config.get('llm', {}).get('ollama_model', ''),
                    help="Model name for chat (e.g., llama3.2)"
                )

            with col2:
                ollama_embedding_model = st.text_input(
                    "Embedding Model",
                    value=config.get('llm', {}).get('ollama_embedding_model', ''),
                    help="Model name for embeddings (e.g., nomic-embed-text)"
                )

                ollama_vision_model = st.text_input(
                    "Vision Model",
                    value=config.get('vision', {}).get('ollama_vision_model', ''),
                    help="Model name for vision tasks (e.g., llama3.2-vision)"
                )

            st.info("💡 Ollama is free (local execution). No API costs.")

            submitted = st.form_submit_button("💾 Save Ollama Settings", use_container_width=True)

            if submitted:
                st.warning("⚠️ Configuration update requires backend restart")
                st.info("Note: This demo shows the UI. Actual configuration updates would require backend API endpoints.")

        # Display current settings
        with st.expander("📋 Current Settings", expanded=True):
            ollama_config = {
                "base_url": config.get('llm', {}).get('ollama_base_url', ''),
                "model": config.get('llm', {}).get('ollama_model', ''),
                "embedding_model": config.get('llm', {}).get('ollama_embedding_model', ''),
                "vision_model": config.get('vision', {}).get('ollama_vision_model', ''),
                "available": config.get('provider_status', {}).get('ollama_available', False),
                "vision_available": config.get('provider_status', {}).get('ollama_vision_available', False)
            }
            st.json(ollama_config)

        # Provider status
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if config.get('provider_status', {}).get('ollama_available', False):
                st.success("✅ Ollama LLM Available")
            else:
                st.error("❌ Ollama LLM Not Available")
        with col2:
            if config.get('provider_status', {}).get('ollama_vision_available', False):
                st.success("✅ Ollama Vision Available")
            else:
                st.error("❌ Ollama Vision Not Available")

    # === RAG CONFIGURATION ===
    with tab3:
        st.subheader("RAG (Retrieval-Augmented Generation) Configuration")
        st.markdown("Configure document processing and retrieval settings")

        with st.form("rag_config_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Document Processing**")

                chunk_size = st.number_input(
                    "Chunk Size",
                    min_value=100,
                    max_value=5000,
                    value=config.get('rag', {}).get('chunk_size', 1000),
                    step=100,
                    help="Size of text chunks for processing"
                )

                chunk_overlap = st.number_input(
                    "Chunk Overlap",
                    min_value=0,
                    max_value=500,
                    value=config.get('rag', {}).get('chunk_overlap', 200),
                    step=50,
                    help="Overlap between consecutive chunks"
                )

                max_upload_size = st.number_input(
                    "Max Upload Size (MB)",
                    min_value=1,
                    max_value=100,
                    value=int(config.get('ocr', {}).get('max_file_size_mb', 10)),
                    step=1,
                    help="Maximum file size for uploads"
                )

            with col2:
                st.markdown("**Retrieval Settings**")

                max_retrieval_docs = st.number_input(
                    "Max Retrieval Documents",
                    min_value=1,
                    max_value=20,
                    value=config.get('rag', {}).get('max_retrieval_docs', 5),
                    step=1,
                    help="Maximum number of documents to retrieve"
                )

                similarity_threshold = st.number_input(
                    "Similarity Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=config.get('rag', {}).get('similarity_threshold', 0.01),
                    step=0.01,
                    format="%.2f",
                    help="Minimum similarity score for retrieval"
                )

                st.markdown("**Vector Store**")
                chroma_collection = st.text_input(
                    "ChromaDB Collection",
                    value=config.get('rag', {}).get('chroma_collection_name', 'rag_documents'),
                    help="ChromaDB collection name"
                )

            st.markdown("**OCR Settings**")
            ocr_confidence = st.slider(
                "OCR Confidence Threshold",
                min_value=0.0,
                max_value=1.0,
                value=config.get('ocr', {}).get('confidence_threshold', 0.7),
                step=0.05,
                help="Minimum confidence for OCR results"
            )

            submitted = st.form_submit_button("💾 Save RAG Settings", use_container_width=True)

            if submitted:
                st.warning("⚠️ Configuration update requires backend restart")
                st.success("Settings saved (demo mode)")

        # Display current settings
        with st.expander("📋 Current RAG Settings", expanded=True):
            st.json(config.get('rag', {}))

        # OCR info
        with st.expander("📷 OCR Configuration Details"):
            ocr_config = config.get('ocr', {})
            st.markdown(f"""
            **Supported Formats:** `{', '.join(ocr_config.get('supported_formats', []))}`

            **Max File Size:** {ocr_config.get('max_file_size_mb', 0)} MB

            **Image Max Dimension:** {ocr_config.get('image_max_dimension', 0)}px

            **PDF DPI:** {ocr_config.get('pdf_dpi', 0)}

            **Enable Preprocessing:** {ocr_config.get('enable_preprocessing', False)}
            """)

    # === AGENT CONFIGURATION ===
    with tab4:
        st.subheader("Agent System Configuration")
        st.markdown("Configure multi-agent orchestration settings")

        with st.form("agent_config_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Execution Settings**")

                agent_temperature = st.slider(
                    "Agent Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=config.get('agent', {}).get('temperature', 0.7),
                    step=0.1,
                    help="Creativity level for agent responses"
                )

                max_iterations = st.number_input(
                    "Max Agent Iterations",
                    min_value=1,
                    max_value=50,
                    value=config.get('agent', {}).get('max_iterations', 10),
                    step=1,
                    help="Maximum agent execution iterations"
                )

                enable_memory = st.checkbox(
                    "Enable Agent Memory",
                    value=config.get('agent', {}).get('enable_memory', True),
                    help="Allow agents to maintain context"
                )

            with col2:
                st.markdown("**Explainability Settings**")

                explainability_level = st.selectbox(
                    "Explainability Level",
                    options=['basic', 'detailed', 'debug'],
                    index=['basic', 'detailed', 'debug'].index(
                        config.get('explainability', {}).get('explainability_level', 'detailed')
                    ),
                    help="Level of explainability detail"
                )

                enable_confidence = st.checkbox(
                    "Enable Confidence Scoring",
                    value=config.get('explainability', {}).get('enable_confidence_scoring', True),
                    help="Calculate confidence scores for responses"
                )

                enable_source_attribution = st.checkbox(
                    "Enable Source Attribution",
                    value=config.get('explainability', {}).get('enable_source_attribution', True),
                    help="Track and display source documents"
                )

                enable_reasoning_chains = st.checkbox(
                    "Enable Reasoning Chains",
                    value=config.get('explainability', {}).get('enable_reasoning_chains', True),
                    help="Show agent reasoning process"
                )

            st.markdown("**Available Agent Types**")
            st.info("""
            🔍 **Research Agent**: Searches and retrieves relevant information
            📊 **Analyzer Agent**: Analyzes and processes data
            📝 **Summarizer Agent**: Creates summaries and extracts key points
            ⚓ **Grounding Agent**: Verifies and grounds responses in sources
            💡 **Explainability Agent**: Provides explanations and reasoning
            """)

            submitted = st.form_submit_button("💾 Save Agent Settings", use_container_width=True)

            if submitted:
                st.warning("⚠️ Configuration update requires backend restart")
                st.success("Settings saved (demo mode)")

        # Display current settings
        with st.expander("📋 Current Agent Settings", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Agent Config:**")
                st.json(config.get('agent', {}))
            with col2:
                st.markdown("**Explainability Config:**")
                st.json(config.get('explainability', {}))

    # === FOOTER ===
    st.markdown("---")
    st.markdown("### 📝 Configuration Notes")
    st.info("""
    **Important:**
    - Configuration changes shown here are for demonstration purposes
    - Actual configuration updates require backend API endpoints or direct file/environment variable modifications
    - After updating configuration, restart the backend service for changes to take effect
    - Some settings may require database migrations or vector store reindexing
    """)

    st.warning("""
    **Security Considerations:**
    - API keys should be stored securely in environment variables
    - Never commit sensitive credentials to version control
    - Use separate keys for development and production environments
    - Regularly rotate API keys and access tokens
    """)


if __name__ == "__main__":
    show_llm_config_page()
