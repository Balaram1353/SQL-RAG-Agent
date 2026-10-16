
import pandas as pd
import streamlit as st

from app.agent import answer_question
from app.vector_store import build_index


st.set_page_config(
    page_title="SQL-RAG-Agent",
    page_icon="📊",
    layout="wide",
)

st.title("📊 SQL-RAG-Agent")
st.caption(
    "Ask questions about your database in natural language. "
    "The agent retrieves schema information, generates SQL, "
    "and explains the actual query results."
)

# Keep chat history across Streamlit reruns.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Build the index once and reuse it.
@st.cache_resource
def initialize_agent():
    return build_index()


try:
    with st.spinner("Initializing the agent..."):
        initialize_agent()
except Exception as exc:
    st.error(f"Could not initialize the agent: {exc}")
    st.stop()


with st.sidebar:
    st.header("About this agent")
    st.write("**LLM:** Local Ollama model")
    st.write("**Retrieval:** Schema embeddings")
    st.write("**Database:** SQLite")
    st.write("**Execution:** Read-only SQL")
    st.divider()

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()


# Display the conversation so far.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sql"):
            with st.expander("Generated SQL"):
                st.code(message["sql"], language="sql")

        if message.get("results") is not None:
            with st.expander("Database results", expanded=True):
                st.dataframe(
                    pd.DataFrame(
                        message["results"],
                        columns=message["columns"],
                    ),
                    use_container_width=True,
                )

        if message.get("attempts") is not None:
            st.caption(
                f"SQL attempts: {message['attempts']}"
            )


question = st.chat_input(
    "Ask a question, e.g. Which product generated the highest revenue?"
)


if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your question..."):
            try:
                response = answer_question(question)

                if not isinstance(response, dict):
                    st.error("Agent returned an unexpected response.")
                    st.write(repr(response))
                    st.stop()

                # Display generated SQL independently.
                sql = response.get("sql", "")
                if sql:
                    with st.expander("Generated SQL", expanded=True):
                        st.code(sql, language="sql")

                # Display the answer.
                answer = response.get("answer", "")
                if answer:
                    st.markdown(answer)

                # Display errors returned by the agent.
                if response.get("error"):
                    st.error(str(response["error"]))

                # Display results independently.
                results = response.get("results")
                columns = response.get("columns")

                if results is not None and columns is not None:
                    with st.expander(
                        "Database results", expanded=True
                    ):
                        df = pd.DataFrame(
                            results, columns=columns
                        )
                        st.write(f"Rows returned: {len(df)}")
                        st.dataframe(
                            df,
                            use_container_width=True,
                        )

                attempts = response.get("attempts")
                if attempts is not None:
                    st.caption(f"SQL attempts: {attempts}")

                # Save the complete response for chat history.
                assistant_message = {
                    "role": "assistant",
                    "content": answer or str(response.get("error", "")),
                    "sql": sql,
                    "results": results,
                    "columns": columns,
                    "attempts": attempts,
                }
                st.session_state.messages.append(
                    assistant_message
                )

            except Exception as exc:
                st.exception(exc)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Something went wrong: {exc}",
                })
