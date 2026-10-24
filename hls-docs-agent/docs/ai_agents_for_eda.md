# Applying LLM Agents to EDA Workflows

EDA toolchains generate large amounts of structured and semi-structured output — log
files, timing reports, synthesis summaries, error messages tied to specific source
lines. This makes them a good fit for LLM-based agents that can read that output,
correlate it against source code and documentation, and surface a plain-language
explanation or suggested fix.

## Typical agent design

An agent built for this kind of task generally has three parts:

1. **Retrieval**: a vector store or search index over documentation, past issue
   resolutions, and coding guidelines, so the agent can ground its answers in real
   material instead of guessing.
2. **Tools**: functions the agent can call, such as searching the documentation index,
   reading a specific file, or querying build/regression status.
3. **A reasoning loop**: the agent decides which tool to call based on the user's
   question, inspects the result, and either calls another tool or produces a final
   answer, repeating until it has enough information.

## Why grounding matters

Without retrieval, an LLM answering a question about a specific tool's directive syntax
or error code is guessing from general training data, which is often wrong for
tool-specific or versioned behavior. Grounding the agent's answers in the team's actual
documentation and past examples — a retrieval-augmented generation (RAG) pipeline —
makes answers traceable back to a source and much more likely to be correct.

## Packaging agent behavior as reusable workflows

Once an agent's reasoning pattern for a specific task works well, it's common to package
it as a reusable "skill" or slash command: a fixed prompt template plus the specific
tools and retrieval sources needed for that task, so any engineer can invoke it
consistently rather than re-explaining the task from scratch each time.
