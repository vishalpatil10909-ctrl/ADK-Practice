import os
import json
from pathlib import Path

from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext

from .config import OPENROUTER_API_KEY

# Set OpenRouter API key
if OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY


MODEL = "openrouter/cohere/north-mini-code:free"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def load_sow_document(file_path: str) -> str:
    """Load a Statement of Work (SOW) from a .txt/.md, .pdf, or .docx file.

    Use this tool only when the user supplies a path to a document. If the user
    pastes the SOW text directly in the chat, do NOT call this tool; parse the
    pasted text instead.

    Args:
        file_path (str): Absolute or relative path to the SOW document.

    Returns:
        str: The extracted plain text of the document, or an error message
        prefixed with "ERROR:" if the file cannot be read.
    """
    path = Path(os.path.expanduser(file_path.strip()))
    if not path.exists():
        return f"ERROR: File not found at '{file_path}'."

    suffix = path.suffix.lower()
    try:
        if suffix in (".txt", ".md"):
            return path.read_text(encoding="utf-8", errors="replace")

        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            pages = [(page.extract_text() or "") for page in reader.pages]
            text = "\n".join(pages).strip()
            return text or "ERROR: No extractable text found in the PDF."

        if suffix == ".docx":
            import docx

            document = docx.Document(str(path))
            paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs).strip()
            return text or "ERROR: No extractable text found in the DOCX."

        return (
            f"ERROR: Unsupported file type '{suffix}'. "
            "Supported formats: .txt, .md, .pdf, .docx."
        )
    except Exception as exc:  # noqa: BLE001 - surface any parsing failure to the agent
        return f"ERROR: Failed to read '{file_path}': {exc}"


def get_gcp_service_catalog() -> str:
    """Return a curated catalog of Google Cloud Platform services by category.

    Each service lists an "ideal_use_case" to help select services that best fit
    the business and technical requirements. Always consult this catalog before
    proposing or revising a cloud architecture blueprint.

    Returns:
        str: A JSON string mapping category -> list of {name, ideal_use_case}.
    """
    catalog = {
        "Compute": [
            {"name": "Cloud Run", "ideal_use_case": "Serverless stateless containers, HTTP APIs, event-driven microservices with scale-to-zero."},
            {"name": "Google Kubernetes Engine (GKE)", "ideal_use_case": "Container orchestration for complex microservices needing fine-grained control."},
            {"name": "Compute Engine", "ideal_use_case": "Full-control VMs, legacy/lift-and-shift workloads, custom OS or GPU needs."},
            {"name": "Cloud Functions", "ideal_use_case": "Lightweight single-purpose event handlers and glue logic."},
            {"name": "App Engine", "ideal_use_case": "Fully managed PaaS for standard web apps without infra management."},
        ],
        "Storage": [
            {"name": "Cloud Storage", "ideal_use_case": "Object storage for files, backups, static assets, data lake landing zones."},
            {"name": "Filestore", "ideal_use_case": "Managed NFS file shares for apps needing a shared POSIX filesystem."},
            {"name": "Persistent Disk", "ideal_use_case": "Block storage attached to Compute Engine/GKE workloads."},
        ],
        "Databases": [
            {"name": "Cloud SQL", "ideal_use_case": "Managed MySQL/PostgreSQL/SQL Server for standard relational workloads."},
            {"name": "AlloyDB", "ideal_use_case": "High-performance PostgreSQL-compatible DB for demanding transactional + analytical workloads."},
            {"name": "Cloud Spanner", "ideal_use_case": "Globally distributed, horizontally scalable, strongly consistent relational DB."},
            {"name": "Firestore", "ideal_use_case": "Serverless document NoSQL for mobile/web apps with realtime sync."},
            {"name": "Bigtable", "ideal_use_case": "Low-latency wide-column NoSQL for high-throughput time-series/IoT data."},
            {"name": "Memorystore", "ideal_use_case": "Managed Redis/Memcached for caching and low-latency lookups."},
        ],
        "Data & Analytics": [
            {"name": "BigQuery", "ideal_use_case": "Serverless data warehouse for large-scale analytics and BI."},
            {"name": "Dataflow", "ideal_use_case": "Unified stream and batch data processing (Apache Beam)."},
            {"name": "Pub/Sub", "ideal_use_case": "Global messaging/event ingestion for decoupled, async architectures."},
            {"name": "Dataproc", "ideal_use_case": "Managed Spark/Hadoop for existing big-data pipelines."},
        ],
        "AI & ML": [
            {"name": "Vertex AI", "ideal_use_case": "End-to-end ML training, serving, and access to foundation models."},
            {"name": "Document AI", "ideal_use_case": "Extract structured data from documents (forms, invoices, contracts)."},
        ],
        "Networking": [
            {"name": "Virtual Private Cloud (VPC)", "ideal_use_case": "Private network isolation and segmentation for all resources."},
            {"name": "Cloud Load Balancing", "ideal_use_case": "Global/regional traffic distribution across backends."},
            {"name": "Cloud CDN", "ideal_use_case": "Edge caching of static/dynamic content for low latency."},
            {"name": "API Gateway", "ideal_use_case": "Managed gateway for exposing and securing serverless/backends APIs."},
            {"name": "Cloud Armor", "ideal_use_case": "DDoS protection and WAF rules at the edge."},
        ],
        "Security & Operations": [
            {"name": "IAM", "ideal_use_case": "Fine-grained access control and least-privilege permissions."},
            {"name": "Secret Manager", "ideal_use_case": "Secure storage and rotation of API keys, passwords, and secrets."},
            {"name": "Cloud KMS", "ideal_use_case": "Managed encryption key creation and control."},
            {"name": "Cloud Monitoring & Logging", "ideal_use_case": "Observability: metrics, dashboards, alerting, and centralized logs."},
        ],
    }
    return json.dumps(catalog, indent=2)


def record_feedback(feedback: str, tool_context: ToolContext) -> str:
    """Record a structured critique for the architecture_builder to address.

    Call this when the blueprint needs improvement. The feedback is appended to
    the running feedback_history so the builder can revise on the next loop.

    Args:
        feedback (str): A highly structured critique payload listing every issue
            and the concrete optimization required.

    Returns:
        str: Confirmation that the feedback was recorded.
    """
    history = tool_context.state.get("feedback_history")
    if not isinstance(history, list):
        history = []
    history.append(feedback)
    tool_context.state["feedback_history"] = history
    return f"Feedback recorded. Total critique entries: {len(history)}."


def approve_architecture(tool_context: ToolContext) -> str:
    """Approve the blueprint and terminate the optimization loop.

    Call this only when the blueprint passes all business and technical criteria.

    Returns:
        str: The terminal status string.
    """
    tool_context.actions.escalate = True
    return "STATUS: OPTIMIZED"


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
intent_spec_extractor = Agent(
    name="intent_spec_extractor",
    model=LiteLlm(model=MODEL),
    description="Parses an arbitrary SOW into a centralized project specification payload.",
    output_key="project_spec",
    tools=[load_sow_document],
    instruction="""
You are the Intent & Spec Extractor.

INPUT HANDLING:
- If the user provides a path to a document (.txt, .md, .pdf, or .docx), call the
  `load_sow_document` tool with that path to extract the raw SOW text.
- If the user pastes the SOW text directly into the chat, parse that text directly
  and do NOT call any tool.

TASK:
Parse the incoming arbitrary Statement of Work (SOW). Isolate and structure:
- business_goals
- target_user_profiles
- technical_stack_requirements
- scope_boundaries (explicitly in-scope and out-of-scope items)
- non_functional_requirements (scale, latency, compliance, budget if stated)

Output ONLY a single JSON object with exactly these keys:
{
  "business_goals": [],
  "target_user_profiles": [],
  "technical_stack_requirements": [],
  "scope_boundaries": {"in_scope": [], "out_of_scope": []},
  "non_functional_requirements": []
}

Do not invent requirements that are not present. If something is unspecified,
use an empty list or note "not specified". Do not include markdown or explanations.
Your output is stored under the key "project_spec".
""",
)

architecture_builder = Agent(
    name="architecture_builder",
    model=LiteLlm(model=MODEL),
    description="Generates or revises a GCP cloud architecture blueprint.",
    output_key="current_blueprint",
    tools=[get_gcp_service_catalog],
    instruction="""
You are the Architecture Builder for Google Cloud Platform (GCP).

Project Specification:
{project_spec}

Previous Blueprint (may be empty on the first pass):
{current_blueprint?}

Critique Log / Feedback History (may be empty on the first pass):
{feedback_history?}

STEP 1: ALWAYS call the `get_gcp_service_catalog` tool first to see which GCP
services are available and their ideal use cases.

STEP 2: Decide the mode:
- If the feedback history is EMPTY, generate the INITIAL baseline GCP architecture.
- If the feedback history contains entries, read the previous blueprint, analyze
  every critique entry, and output a REVISED, optimized blueprint that explicitly
  addresses each point.

RULES FOR SERVICE SELECTION:
- Only choose services from the catalog.
- Select the services that IDEALLY fit the business goals and technical
  requirements; justify each choice in one line referencing the requirement it serves.
- Prefer managed/serverless options unless the requirements call for more control.

OUTPUT (Markdown):
# GCP Architecture Blueprint
## Selected Services
- <Service> (<Category>): <one-line justification tied to a requirement>
## Architecture Overview
<How the services connect: request flow, data flow, storage, security, scaling.>
## Requirements Coverage
<Map each business/technical requirement to the service(s) that satisfy it.>
## Changes Since Last Revision
<If revising, list how each feedback point was addressed. Otherwise write "Initial baseline.">

Your output is stored under the key "current_blueprint".
""",
)

reviewer_critic_agent = Agent(
    name="reviewer_critic_agent",
    model=LiteLlm(model=MODEL),
    description="Reviews the blueprint and either records feedback or approves it.",
    tools=[record_feedback, approve_architecture],
    instruction="""
You are the Reviewer & Critic Agent, the quality gate for the architecture loop.

Project Specification:
{project_spec}

Proposed Blueprint:
{current_blueprint}

Existing Feedback History:
{feedback_history?}

Review the proposed blueprint against the business intent and technical
constraints in the project specification. Evaluate:
- Coverage: Are ALL business goals and technical requirements addressed?
- Service fit: Are the chosen GCP services ideal, or is there a better option?
- Cost, scalability, security, and operational soundness.
- Whether it respects the stated scope boundaries.

DECISION:
- If you find ANY optimization or gap, call `record_feedback` with a highly
  structured critique payload that lists each issue and the concrete change
  required. Do NOT call `approve_architecture` in this case.
- If the blueprint passes ALL criteria, call `approve_architecture` (which returns
  "STATUS: OPTIMIZED") to break the loop.

Call exactly one tool per turn. Do not rewrite the blueprint yourself.
""",
)


diagram_generator = Agent(
    name="diagram_generator",
    model=LiteLlm(model=MODEL),
    description="Renders the approved GCP blueprint as a Mermaid architecture diagram.",
    output_key="architecture_diagram",
    instruction="""
You are the Diagram Generator. The optimization loop has finished and produced an
approved GCP architecture blueprint.

Approved Blueprint:
{current_blueprint}

TASK:
Produce a Mermaid `flowchart` that visualizes the architecture in the blueprint,
grouping services into layers (e.g. User Interface, Backend/Application, Data &
Platform) using subgraphs, and drawing the request/data flow between them.

STRICT MERMAID SYNTAX RULES (follow exactly or the diagram will not render):
- Start the code block with ```mermaid and end it with ```.
- Use `flowchart TD` (top-down) or `flowchart LR` (left-right).
- Node IDs must be single tokens with NO spaces (use camelCase or underscores).
  Put the human-readable label in brackets: `cloudRun["Cloud Run (API)"]`.
- Wrap any label containing spaces, parentheses, colons, or commas in double quotes.
- Subgraphs: `subgraph layerId ["Layer Label"]` ... `end`.
- Do NOT use reserved IDs like `end`, `graph`, `subgraph`.
- Do NOT add colors, `style`, `classDef`, or `click` directives.
- Only reference GCP services that appear in the approved blueprint.

OUTPUT:
1. First, one short sentence introducing the diagram.
2. Then the single ```mermaid code block``` and nothing after it.

The diagram is stored under the key "architecture_diagram".
""",
)


# ---------------------------------------------------------------------------
# Workflow assembly
# ---------------------------------------------------------------------------
refinement_loop = LoopAgent(
    name="refinement_loop",
    description="Iteratively optimizes the GCP blueprint until approved or max loops.",
    sub_agents=[architecture_builder, reviewer_critic_agent],
    max_iterations=3,
)

sow_pipeline = SequentialAgent(
    name="sow_pipeline",
    description="Turns an arbitrary SOW into an optimized GCP architecture blueprint and a Mermaid diagram.",
    sub_agents=[intent_spec_extractor, refinement_loop, diagram_generator],
)

root_agent = Agent(
    name="sow_planner_root",
    model=LiteLlm(model=MODEL),
    description="Front door: greets the user and routes valid SOWs into the GCP planning pipeline.",
    sub_agents=[sow_pipeline],
    instruction="""
You are the front door of an SOW to GCP Architecture Planner.

Your ONLY job is to decide intent. Do NOT design architectures, parse SOWs, or
list GCP services yourself.

DECISION RULES:
1. If the user's message is a greeting, small talk, or a general question about
   what you do (e.g. "hi", "hello", "hey", "what can you do?"):
   - Reply DIRECTLY (do not transfer) with a short, friendly greeting that
     explains you turn a Statement of Work (SOW) into an optimized Google Cloud
     (GCP) architecture blueprint.
   - Ask the user to either paste their SOW text directly, or provide a path to a
     .txt, .md, .pdf, or .docx file containing the SOW.

2. If the user's message contains an actual SOW (business goals, technical/stack
   requirements, scope, or a project description) OR a path to a document file:
   - Transfer control to `sow_pipeline` to run the extraction and optimization
     loop. Do NOT announce the transfer and do NOT add commentary.

3. If you are unsure whether the text is a real SOW (it is too short or vague to
   plan against):
   - Ask ONE brief clarifying question instead of transferring.

Never run the pipeline for a simple greeting.
""",
)
