from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import torch
import logging
import math
from aethelnet.liquid_graph import LiquidGraph
from lgnn.command_chain_builder import synthesize_command_chain, run_dry_run_chain
from lgnn.mcp_protocol import get_mcp_tools, call_mcp_tool
from lgnn.command_replanner import generate_command_plan
from lgnn.coherence_checker import evaluate_graph_coherence
from lgnn.database import (
    register_agent, log_cooperation, get_agent_history,
    init_db, save_node, delete_node, save_edge, delete_edge,
    load_graph_state, save_kanban_card, load_kanban_board, get_node_text,
    save_persona, load_personas, search_archived_nodes, unarchive_node
)

logger = logging.getLogger("LGNN.Router")

router = APIRouter(prefix="/api/lgnn", tags=["lgnn"])

# Initialize LGNN dimensions and database
hidden_dim = 128
init_db()

# Instantiate the global graph
graph_instance = LiquidGraph(hidden_dim=hidden_dim, resonance_threshold=0.5, decay_rate=0.01)

from lgnn.command_parser import get_parsed_command_node_content
from lgnn.web_search import search_wikipedia
from lgnn.command_runner import run_command_safely
from lgnn.living_loop import tick_ecosystem_loop
from lgnn.research_scouter import scout_arxiv_optimizations

# Reality Anchors (Physical Constants to ground the AI reality)
REALITY_ANCHORS = {}

# Node-specific metrics cache
node_metrics: Dict[str, Dict[str, Any]] = {}

def load_all_from_db():
    """
    Loads saved state from database or seeds defaults if empty.
    """
    global node_metrics
    nodes, edges, metrics = load_graph_state(dim=hidden_dim)
    
    if not nodes:
        logger.info("[LGNN] Database empty. Seeding default reality anchors...")
        # Add default reality anchors
        for anchor_name, info in REALITY_ANCHORS.items():
            anchor_text = f"{anchor_name}: {info['desc']} value={info['value']}"
            torch.manual_seed(hash(anchor_name) % (2**32 - 1))
            emb = torch.randn(hidden_dim)
            emb = emb / (emb.norm() + 1e-8)
            
            # Save in-memory
            graph_instance.add_node(anchor_name, emb)
            # Save in database
            save_node(anchor_name, emb, 0.0, 0.95, 0.0, True, False, text_content=anchor_text)
            
        # Seed default Kanban Tasks
        default_cards = [
            ("task-1", "backlog", "Luhmann Footnote Parser", "Extract semantic references from systems theory footnotes.", ["seed"], "Gravity Constant (g)"),
            ("task-2", "todo", "Integrate 3D Super Paper Mario Switch", "Build frontend switch to flip graph from 2D physics into 3D space.", ["canvas", "3d"], None),
            ("task-3", "in_progress", "Hebbian Bridge Calibration", "Tune resonance threshold for dynamic synaptic pruning.", ["math"], None),
            ("task-4", "done", "LiquidNode ODE Solver", "Verify rk4 solver integration with torchdiffeq.", ["neural"], None)
        ]
        for card_id, col, title, desc, tags, node_ref in default_cards:
            save_kanban_card(card_id, col, title, desc, tags, node_ref)
            
        # Reload
        nodes, edges, metrics = load_graph_state(dim=hidden_dim)
        
    # Sync memory state with loaded DB items
    graph_instance.nodes.clear()
    graph_instance.nx_graph.clear()
    
    for nid, emb in nodes.items():
        graph_instance.add_node(nid, emb)
        
    for u, v, weight, label, embedding in edges:
        if u in graph_instance.nodes and v in graph_instance.nodes:
            graph_instance.nx_graph.add_edge(u, v, weight=weight, label=label, embedding=embedding)
            
    # Sync Personas
    personas, active_status = load_personas()
    graph_instance.personas = personas
    graph_instance.active_personas = active_status
            
    node_metrics = metrics
    logger.info(f"[LGNN] Loaded {len(nodes)} nodes, {len(edges)} bridges, and {len(personas)} personas from SQLite.")

# Load state on startup
load_all_from_db()

class NodeCreate(BaseModel):
    id: str
    text_content: str
    connections: Optional[List[str]] = []
    source_tag: Optional[str] = "internal"
    is_quarantined: Optional[bool] = False
    is_shielded: Optional[bool] = False

class UniversalIngest(BaseModel):
    bot_name: str
    observation: str
    confidence: Optional[float] = 0.8
    context_tags: Optional[List[str]] = []
    node_prefix: Optional[str] = None

class CardMove(BaseModel):
    card_id: str
    source_col: str
    target_col: str

class CommandRunRequest(BaseModel):
    command: str
    cwd: Optional[str] = None

class CommandChainRequest(BaseModel):
    source_cmd: str
    target_cmd: str
    options: Optional[Dict[str, Any]] = None

class McpToolCallRequest(BaseModel):
    name: str
    arguments: Optional[Dict[str, Any]] = {}

class AgentRegisterRequest(BaseModel):
    agent_id: str
    metadata: Dict[str, Any]

class AgentCooperateRequest(BaseModel):
    agent_id: str
    requested_skill: str
    success: bool
    notes: str

class PersonaDefineRequest(BaseModel):
    name: str
    node_ids: List[str]

class PersonaActivateRequest(BaseModel):
    name: str
    active: bool

class CommandPlanRequest(BaseModel):
    task_key: str
    banned_utilities: List[str]

class CoherenceRequest(BaseModel):
    prioritized_nodes: List[str]

def text_to_embedding(text: str, dim: int = 128) -> torch.Tensor:
    torch.manual_seed(hash(text) % (2**32 - 1))
    raw_emb = torch.randn(dim)
    return raw_emb / (raw_emb.norm() + 1e-8)

@router.get("/graph")
async def get_graph():
    nodes_data = []
    links_data = []
    
    node_ids = list(graph_instance.nodes.keys())
    for nid in node_ids:
        state_tensor = graph_instance.nodes[nid]
        mean_activation = float(state_tensor.mean().detach().cpu())
        if math.isnan(mean_activation) or math.isinf(mean_activation):
            mean_activation = 0.0
        
        # Resolve metrics or use defaults
        metrics = node_metrics.setdefault(nid, {
            "confidence": 0.95,
            "plateau_factor": 0.0,
            "is_grounded": nid in REALITY_ANCHORS,
            "help_chain": nid.startswith("CMD:"),
            "source_tag": "internal",
            "is_quarantined": False
        })
        
        # Fetch actual text from database
        content = get_node_text(nid) or ""
        
        # Try to derive a readable label from the content if it's a hash ID
        label = nid
        if nid.startswith("n_") and len(content.strip()) > 0:
            label = content.strip().split("\n")[0][:30] + "..."
        
        nodes_data.append({
            "id": nid,
            "label": label,
            "content": content,
            "mean_activation": mean_activation,
            "size": 15 + abs(mean_activation) * 10,
            "confidence": metrics["confidence"],
            "plateau_factor": metrics["plateau_factor"],
            "is_grounded": metrics["is_grounded"],
            "help_chain": metrics["help_chain"],
            "source_tag": metrics["source_tag"],
            "is_quarantined": metrics["is_quarantined"]
        })
        
    for u, v, data in graph_instance.nx_graph.edges(data=True):
        weight = float(data.get('weight', 1.0))
        if math.isnan(weight) or math.isinf(weight):
            weight = 0.0
        links_data.append({
            "source": u,
            "target": v,
            "weight": weight
        })
        
    return {"nodes": nodes_data, "links": links_data}

def get_lgnn_galaxy_topology():
    """Converts LGNN graph state into the Galaxy Map format for frontend visualization."""
    nodes_data = []
    links_data = []
    
    node_ids = list(graph_instance.nodes.keys())
    for nid in node_ids:
        state_tensor = graph_instance.nodes[nid]
        mean_act = float(state_tensor.mean().detach().cpu())
        if math.isnan(mean_act) or math.isinf(mean_act):
            mean_act = 0.0
            
        metrics = node_metrics.get(nid, {})
        
        # Map attributes to the Galaxy requirements
        is_anchor = metrics.get("is_grounded", False)
        is_cmd = metrics.get("help_chain", False)
        
        if is_anchor:
            node_type = "singularity"
            color = "#000000"
            tier = -1
        elif is_cmd:
            node_type = "market"
            color = "#f59e0b"
            tier = 0
        else:
            node_type = "symbol"
            color = "#3b82f6"
            tier = 1
            
        base_rad = 10 + abs(mean_act) * 20
            
        nodes_data.append({
            "id": nid,
            "label": nid,
            "type": node_type,
            "tier": tier,
            "color": color,
            "baseRadius": base_rad,
            "currentRadius": base_rad,
            "data": { "activation": mean_act, "confidence": metrics.get("confidence", 0) }
        })
        
    for u, v, data in graph_instance.nx_graph.edges(data=True):
        weight = float(data.get('weight', 1.0))
        if math.isnan(weight) or math.isinf(weight):
            weight = 0.0
        links_data.append({
            "source": u,
            "target": v,
            "weight": weight
        })
        
    return {"nodes": nodes_data, "links": links_data, "physics_config": {"repulsion": 350}}

@router.post("/node")
async def create_node(data: NodeCreate):
    content = data.text_content
    is_anchor = data.id in REALITY_ANCHORS
    is_cmd = data.id.startswith("CMD:")
    
    if is_cmd:
        # Extract command name (e.g. "CMD: find --help" -> "find")
        cmd_part = data.id.replace("CMD:", "").strip()
        cmd_tokens = cmd_part.split()
        if cmd_tokens:
            cmd_name = cmd_tokens[0]
            parsed_content = get_parsed_command_node_content(cmd_name)
            if "Error" not in parsed_content:
                content = parsed_content
                
    emb = text_to_embedding(content, dim=hidden_dim)
    graph_instance.add_node(data.id, emb, connections=data.connections)
    
    if getattr(data, 'is_shielded', False):
        if not hasattr(graph_instance, 'nodes_meta'):
            graph_instance.nodes_meta = {}
        if data.id not in graph_instance.nodes_meta:
            graph_instance.nodes_meta[data.id] = {}
        graph_instance.nodes_meta[data.id]["is_shielded"] = True
    
    # Initialize metrics
    # Initialize metrics
    node_metrics[data.id] = {
        "confidence": 0.8,
        "plateau_factor": 0.0,
        "is_grounded": is_anchor,
        "help_chain": is_cmd,
        "source_tag": data.source_tag,
        "is_quarantined": data.is_quarantined
    }
    
    # Persist Node with parsed text content
    save_node(data.id, emb, 0.0, 0.8, 0.0, is_anchor, is_cmd, text_content=content, source_tag=data.source_tag, is_quarantined=data.is_quarantined)
    
    # Persist explicit initial connections
    if data.connections:
        for conn in data.connections:
            if conn in graph_instance.nodes:
                save_edge(data.id, conn, 1.0)
                
from lgnn.database import enqueue_observation, dequeue_observation, mark_observation_done
import json

async def process_ingestion_queue():
    import hashlib
    import asyncio
    while True:
        try:
            job_id, payload_json = dequeue_observation()
            if not job_id:
                await asyncio.sleep(1) # Wait for new jobs
                continue
                
            data_dict = json.loads(payload_json)
            
            # Generate a deterministic but unique ID
            prefix = data_dict.get('node_prefix') or f"Import_{data_dict['bot_name']}"
            obs_hash = hashlib.md5(data_dict['observation'].encode()).hexdigest()[:8]
            node_id = f"{prefix}_{obs_hash}"
            
            emb = text_to_embedding(data_dict['observation'], dim=hidden_dim)
            graph_instance.add_node(node_id, emb, connections=[])
            
            node_metrics[node_id] = {
                "confidence": data_dict['confidence'],
                "plateau_factor": 0.0,
                "is_grounded": False,
                "help_chain": False,
                "source_tag": f"external_bot_{data_dict['bot_name']}",
                "is_quarantined": False
            }
            
            save_node(
                node_id=node_id, 
                embedding=emb, 
                mean_activation=0.0, 
                confidence=data_dict['confidence'], 
                plateau_factor=0.0, 
                is_grounded=False, 
                help_chain=False, 
                text_content=f"[{','.join(data_dict['context_tags'])}] {data_dict['observation']}", 
                source_tag=f"external_bot_{data_dict['bot_name']}", 
                is_quarantined=False
            )
            
            mark_observation_done(job_id)
            
        except Exception as e:
            logger.error(f"Error in mass ingest queue: {e}")
            await asyncio.sleep(1)

import asyncio
# Start the background task when module loads
asyncio.get_event_loop().create_task(process_ingestion_queue())

@router.post("/universal_ingest")
async def universal_ingestion(data: UniversalIngest):
    """
    A dead-simple endpoint for ANY external AI (Trading bots, Discord bots, LLM scripts) 
    to dump knowledge into the LGNN. Now uses the Async Hygiene Protocol + Postgres SKIP LOCKED!
    """
    # 🚀 Push to Postgres Queue (No Redis needed!)
    enqueue_observation(data.json())
    
    return {"status": "queued", "message": "Observation added to the Postgres Mass-Ingestion Queue."}

@router.delete("/node/{node_id}")
async def remove_node_endpoint(node_id: str):
    if node_id not in graph_instance.nodes:
        raise HTTPException(status_code=404, detail="Node not found")
    
    graph_instance.remove_node(node_id)
    if node_id in node_metrics:
        del node_metrics[node_id]
        
    # SQLite Cascading handles edge deletion
    delete_node(node_id)
    return {"status": "success", "node_id": node_id}

@router.get("/node/{node_id}")
async def get_node_content_endpoint(node_id: str):
    if node_id not in graph_instance.nodes:
        raise HTTPException(status_code=404, detail="Node not found")
    text = get_node_text(node_id)
    return {"id": node_id, "text_content": text}

@router.post("/command/run")
async def run_command_endpoint(data: CommandRunRequest):
    res = run_command_safely(data.command, data.cwd)
    return res

@router.post("/command/chain")
async def build_command_chain_endpoint(data: CommandChainRequest):
    res = synthesize_command_chain(data.source_cmd, data.target_cmd, data.options)
    return res

@router.get("/mcp/tools")
async def mcp_tools_list_endpoint():
    return {"tools": get_mcp_tools()}

@router.post("/mcp/tools/call")
async def mcp_tool_call_endpoint(data: McpToolCallRequest):
    res = call_mcp_tool(data.name, data.arguments)
    return res

@router.post("/command/plan")
async def get_command_plan_endpoint(data: CommandPlanRequest):
    res = generate_command_plan(data.task_key, data.banned_utilities)
    return res

@router.post("/coherence/evaluate")
async def evaluate_coherence_endpoint(data: CoherenceRequest):
    res = evaluate_graph_coherence(data.prioritized_nodes, hidden_dim=hidden_dim)
    return res

@router.post("/mcp/agent/register")
async def mcp_agent_register_endpoint(data: AgentRegisterRequest):
    register_agent(data.agent_id, data.metadata)
    return {"status": "success", "message": f"Agent '{data.agent_id}' registered successfully."}

@router.post("/mcp/agent/cooperate")
async def mcp_agent_cooperate_endpoint(data: AgentCooperateRequest):
    log_cooperation(data.agent_id, data.requested_skill, data.success, data.notes)
    return {"status": "success", "message": "Cooperation history logged."}

@router.get("/mcp/agent/{agent_id}/history")
async def mcp_agent_history_endpoint(agent_id: str):
    history = get_agent_history(agent_id)
    return {"agent_id": agent_id, "history": history}

@router.get("/persona")
async def get_personas_endpoint():
    return {
        "personas": graph_instance.personas,
        "active_status": graph_instance.active_personas
    }

@router.post("/persona/define")
async def define_persona_endpoint(data: PersonaDefineRequest):
    # Enforce that nodes exist
    for nid in data.node_ids:
        if nid not in graph_instance.nodes:
            raise HTTPException(status_code=400, detail=f"Node '{nid}' does not exist in graph topology.")
            
    graph_instance.define_persona(data.name, data.node_ids)
    save_persona(data.name, data.node_ids, False)
    return {"status": "success", "message": f"Persona '{data.name}' defined."}

@router.post("/persona/activate")
async def activate_persona_endpoint(data: PersonaActivateRequest):
    if data.name not in graph_instance.personas:
        raise HTTPException(status_code=404, detail="Persona not found")
        
    graph_instance.set_persona_active(data.name, data.active)
    save_persona(data.name, graph_instance.personas[data.name], data.active)
    return {"status": "success", "message": f"Persona '{data.name}' status updated to {data.active}."}

@router.post("/ecosystem/tick")
async def ecosystem_tick_endpoint():
    res = tick_ecosystem_loop(hidden_dim=hidden_dim)
    return res

@router.post("/ecosystem/scout")
async def ecosystem_scout_endpoint(query: Optional[str] = Query("neural ode graph optimization")):
    res = scout_arxiv_optimizations(query)
    return {"status": "success", "results": res}

@router.post("/evolve")
async def evolve_graph(steps: int = Query(1, ge=1)):
    """
    Evolves continuous ODE states and triggers Hebbian bridge updates.
    All state outputs are serialized back to SQLite.
    """
    for _ in range(steps):
        graph_instance.evolve_topology(compute_time=0.5)
        
    node_ids = list(graph_instance.nodes.keys())
    if len(node_ids) > 1:
        # Calculate cosine similarity matrix
        states = torch.stack([graph_instance.nodes[nid] for nid in node_ids])
        norm_states = states / (states.norm(dim=-1, keepdim=True) + 1e-8)
        similarity_matrix = torch.matmul(norm_states, norm_states.T)
        
        # Apply reality anchoring validation
        for i, nid in enumerate(node_ids):
            if nid in REALITY_ANCHORS:
                continue
                
            metrics = node_metrics.setdefault(nid, {
                "confidence": 0.8, 
                "plateau_factor": 0.0, 
                "is_grounded": False, 
                "help_chain": nid.startswith("CMD:")
            })
            
            # Find closest reality anchor
            max_anchor_sim = 0.0
            for j, anchor_id in enumerate(node_ids):
                if anchor_id in REALITY_ANCHORS:
                    sim = float(similarity_matrix[i, j].detach().cpu())
                    max_anchor_sim = max(max_anchor_sim, sim)
            
            # Update confidence score
            metrics["confidence"] = round(0.5 + (max_anchor_sim * 0.5), 3)
            
            # Plateau detection (averaging neighbor similarities)
            neighbor_sims = []
            for j in range(len(node_ids)):
                if i != j:
                    neighbor_sims.append(float(similarity_matrix[i, j].detach().cpu()))
            
            if neighbor_sims:
                avg_neighbor_sim = sum(neighbor_sims) / len(neighbor_sims)
                if avg_neighbor_sim > 0.85:
                    metrics["plateau_factor"] = min(metrics["plateau_factor"] + 0.15, 1.0)
                else:
                    metrics["plateau_factor"] = max(metrics["plateau_factor"] - 0.1, 0.0)
                    
            # If confidence is low, integrate ODE more intensively
            if metrics["confidence"] < 0.65:
                graph_instance.evolve_topology(compute_time=1.5)
                
    # --- Sync refined state back to SQLite ---
    for nid in node_ids:
        state_tensor = graph_instance.nodes[nid]
        mean_activation = float(state_tensor.mean().detach().cpu())
        m = node_metrics[nid]
        text = get_node_text(nid)
        save_node(nid, state_tensor, mean_activation, m["confidence"], m["plateau_factor"], m["is_grounded"], m["help_chain"], text_content=text)
        
    # Re-sync current edges to SQLite
    # 1. Clear database edges
    conn = SQLite_clear_edges_temp()
    # 2. Write current edges
    for u, v, data in graph_instance.nx_graph.edges(data=True):
        weight = float(data.get('weight', 1.0))
        save_edge(u, v, weight)
        
    # --- AI KANBAN LOOP PERSISTENCE ---
    kanban_board = load_kanban_board()
    for col_id, col in list(kanban_board["columns"].items()):
        for card in list(col["cards"]):
            node_ref = card.get("node_ref")
            if node_ref and node_ref in node_metrics:
                m = node_metrics[node_ref]
                if m["plateau_factor"] > 0.7 and col_id == "todo":
                    # Move card to backlog
                    save_kanban_card(card["id"], "backlog", card["title"], card["description"], card["tags"], node_ref)
                    logger.info(f"[Kanban] Card '{card['title']}' demoted to backlog due to node plateau.")
                elif m["confidence"] < 0.6 and col_id != "backlog":
                    # Refine title
                    if not card["title"].startswith("⚠️ Refine:"):
                        refined_title = f"⚠️ Refine: {card['title']}"
                        save_kanban_card(card["id"], col_id, refined_title, card["description"], card["tags"], node_ref)
                        
    return {"status": "success", "graph": await get_graph(), "kanban": load_kanban_board()}

def SQLite_clear_edges_temp():
    # Helper to purge stale edges in SQLite before rewriting the active evolved graph topology
    from lgnn.database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lgnn_edges")
    conn.commit()
    conn.close()

@router.get("/kanban")
async def get_kanban_endpoint():
    return load_kanban_board()

@router.post("/kanban/move")
async def move_card_endpoint(data: CardMove):
    board = load_kanban_board()
    columns = board["columns"]
    if data.source_col not in columns or data.target_col not in columns:
        raise HTTPException(status_code=400, detail="Invalid column IDs")
        
    card_to_move = None
    for card in columns[data.source_col]["cards"]:
        if card["id"] == data.card_id:
            card_to_move = card
            break
            
    if not card_to_move:
        raise HTTPException(status_code=404, detail="Card not found in source column")
        
    # Save moved card state in SQLite
    save_kanban_card(card_to_move["id"], data.target_col, card_to_move["title"], card_to_move["description"], card_to_move["tags"], card_to_move.get("node_ref"))
    return {"status": "success", "kanban": load_kanban_board()}

@router.post("/web-inject")
async def web_inject_endpoint(query: str = Body(..., embed=True)):
    is_plateau = False
    for nid, m in node_metrics.items():
        if query.lower() in nid.lower() and m["plateau_factor"] > 0.6:
            is_plateau = True
            break
            
    final_query = query
    if is_plateau:
        final_query = f"{query} opposite concepts alternative theories"
        logger.info(f"[LGNN] Plateau detected for '{query}'. Pushing query to '{final_query}'.")
        
    content = search_wikipedia(final_query)
    node_id = f"Search: {query}" if not is_plateau else f"Novel: {query} Alternatives"
    
    emb = text_to_embedding(content, dim=hidden_dim)
    graph_instance.add_node(node_id, emb)
    
    node_metrics[node_id] = {
        "confidence": 0.85,
        "plateau_factor": 0.0,
        "is_grounded": False,
        "help_chain": node_id.startswith("CMD:")
    }
    
    # Save Node to SQLite
    save_node(node_id, emb, 0.0, 0.85, 0.0, False, False, text_content=content)
    
    # Evolve topology to create bridges and save them
    graph_instance.evolve_topology(compute_time=0.5)
    
    # Re-sync current edges to SQLite
    SQLite_clear_edges_temp()
    for u, v, data in graph_instance.nx_graph.edges(data=True):
        weight = float(data.get('weight', 1.0))
        save_edge(u, v, weight)
        
    return {"status": "success", "node_id": node_id, "content": content}

class GenerateResponseRequest(BaseModel):
    prompt: str
    persona: Optional[str] = None
    length: str = "medium" # short, medium, long

class EvolveTextRequest(BaseModel):
    text: str

@router.post("/generate-response")
async def generate_response_endpoint(data: GenerateResponseRequest):
    emb = text_to_embedding(data.prompt, dim=hidden_dim)
    
    # Filter nodes based on active persona if specified
    active_nodes = list(graph_instance.nodes.keys())
    if data.persona and data.persona in graph_instance.personas:
        p_nodes = graph_instance.personas[data.persona]
        if p_nodes:
            active_nodes = [n for n in active_nodes if n in p_nodes]
            
    if not active_nodes:
        return {"status": "error", "message": "No active nodes in selected persona context."}
        
    # Calculate similarities
    node_embs = torch.stack([graph_instance.nodes[n] for n in active_nodes])
    norm_prompt = emb / (emb.norm() + 1e-8)
    norm_nodes = node_embs / (node_embs.norm(dim=-1, keepdim=True) + 1e-8)
    similarities = torch.matmul(norm_nodes, norm_prompt)
    
    # Sort and pick top N
    sim_scores = [(active_nodes[i], float(similarities[i].detach().cpu())) for i in range(len(active_nodes))]
    sim_scores.sort(key=lambda x: x[1], reverse=True)
    
    num_to_pick = 1 if data.length == "short" else 2 if data.length == "medium" else 4
    top_matches = sim_scores[:num_to_pick]
    
    # Extract data for voice module
    top_nodes_data = []
    for nid, score in top_matches:
        top_nodes_data.append({
            "id": nid,
            "text": get_node_text(nid),
            "score": score
        })
        
    # Generate Synthetic Voice Response
    from lgnn.voice import synthesize_voice
    voice_response = synthesize_voice(
        top_nodes_data, 
        prompt=data.prompt,
        persona=data.persona,
        decay_rate=graph_instance.decay_rate
    )
    
    return {
        "status": "success",
        "response": voice_response,
        "matches": [{"node_id": nid, "score": score} for nid, score in top_matches]
    }

@router.post("/evolve-text")
async def evolve_text_endpoint(data: EvolveTextRequest):
    # 1. Advanced Tagging & Concept Extraction via Ollama
    import urllib.request
    import json
    import os
    
    OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    model_name = os.environ.get("OLLAMA_MODEL", "mistral:latest")
    
    tag_prompt = f"Extrahiere 3 bis 5 wissenschaftliche Kernkonzepte (Tags) aus folgendem Text. Antworte NUR mit den Tags, kommagetrennt.\n\nText: {data.text}"
    
    tags = ""
    try:
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/generate",
            data=json.dumps({"model": model_name, "prompt": tag_prompt, "stream": False}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as res:
            tags = json.loads(res.read().decode('utf-8')).get('response', '')
    except Exception:
        tags = "Unclassified"

    # Ingest text as temporary node with advanced tagging
    node_name = tags.split(',')[0].strip()[:30] if tags else "TempNode"
    node_name = node_name.replace('.', '').replace('\n', '').replace('\r', '')
    temp_id = f"{node_name}_{hash(data.text) % 10000}"
    
    # Advanced Embedding (Using the full text + tags for richer latent representation)
    enriched_text = f"Tags: {tags}\n\nContent: {data.text}"
    emb = text_to_embedding(enriched_text, dim=hidden_dim)
    
    # Find initial wiring to the swarm (Initial-Verdrahtung)
    top_3_nodes = []
    if graph_instance.nodes:
        norm_emb = emb / (emb.norm() + 1e-8)
        sims = []
        for nid, nemb in graph_instance.nodes.items():
            norm_nemb = nemb / (nemb.norm() + 1e-8)
            sim = float(torch.dot(norm_emb, norm_nemb).detach().cpu())
            sims.append((nid, sim))
        sims.sort(key=lambda x: x[1], reverse=True)
        top_3_nodes = [nid for nid, sim in sims[:3]]
        
    graph_instance.add_node(temp_id, emb, connections=top_3_nodes)
    node_metrics[temp_id] = {
        "confidence": 0.8,
        "plateau_factor": 0.0,
        "is_grounded": False,
        "help_chain": False
    }
    save_node(temp_id, emb, 0.0, 0.8, 0.0, False, False, text_content=enriched_text)

    # --- Dream Catcher: Subconscious Retrieval ---
    # Search the SQLite archive for dormant nodes that resonate strongly with the new thought
    try:
        awakened = search_archived_nodes(emb, dim=hidden_dim, top_k=2, threshold=0.85)
        for d_node in awakened:
            nid = d_node["id"]
            if nid not in graph_instance.nodes:
                unarchive_node(nid)
                graph_instance.add_node(nid, d_node["embedding"])
                node_metrics[nid] = {
                    "confidence": 0.8,
                    "plateau_factor": 0.0,
                    "is_grounded": False,
                    "help_chain": False
                }
                logger.info(f"🌌 [Dream Catcher] Awakened dormant node '{nid}' from Subconscious Archive.")
    except Exception as e:
        logger.error(f"[Dream Catcher] Failed to scan archive: {e}")

    # Measure initial alignment with reality anchors
    nodes_list = list(graph_instance.nodes.keys())
    anchors = [n for n in nodes_list if node_metrics.get(n, {}).get("is_grounded", False)]
    
    initial_align = {}
    if anchors:
        temp_emb = graph_instance.nodes[temp_id]
        norm_temp = temp_emb / (temp_emb.norm() + 1e-8)
        for anchor in anchors:
            a_emb = graph_instance.nodes[anchor]
            norm_a = a_emb / (a_emb.norm() + 1e-8)
            sim = float(torch.dot(norm_temp, norm_a).detach().cpu())
            initial_align[anchor] = sim
            
    # Evolve topology
    graph_instance.evolve_topology(compute_time=1.5)
    
    # Measure final alignment
    final_align = {}
    if anchors:
        temp_emb = graph_instance.nodes[temp_id]
        norm_temp = temp_emb / (temp_emb.norm() + 1e-8)
        for anchor in anchors:
            a_emb = graph_instance.nodes[anchor]
            norm_a = a_emb / (a_emb.norm() + 1e-8)
            sim = float(torch.dot(norm_temp, norm_a).detach().cpu())
            final_align[anchor] = sim
            
    # Remove temporary node
    graph_instance.remove_node(temp_id)
    delete_node(temp_id)
    
    # Synthesize evolution report
    evolution_lines = [
        "### ⚡ Latent State Evolution Complete",
        f"**Original Text**: \"{data.text[:120]}...\"",
        "",
        "#### Attractor Alignment Analysis:"
    ]
    
    for anchor in anchors:
        init_val = initial_align.get(anchor, 0.0)
        final_val = final_align.get(anchor, 0.0)
        diff = final_val - init_val
        direction = "Pull (+)" if diff > 0 else "Push (-)"
        evolution_lines.append(
            f"- **{anchor}**: Align shifted from {round(init_val * 100, 1)}% to {round(final_val * 100, 1)}% ({direction} {round(abs(diff) * 100, 1)}%)"
        )
        
    evolution_lines.extend([
        "",
        "#### Evolved Hypothesis Output:",
        f"> The concepts presented converged towards nearest attractors, resolving latent contradictions and stabilizing topology. Alignment with Reality Anchors changed by average of {round(sum(final_align.values())/len(final_align) - sum(initial_align.values())/len(initial_align), 3) * 100 if anchors else 0.0}%."
    ])
    
    return {
        "status": "success",
        "evolved_text": "\n".join(evolution_lines)
    }

class SettingsUpdateRequest(BaseModel):
    resonance_threshold: Optional[float] = None
    decay_rate: Optional[float] = None

@router.get("/settings")
async def get_settings_endpoint():
    return {
        "resonance_threshold": graph_instance.resonance_threshold,
        "decay_rate": graph_instance.decay_rate
    }

@router.post("/settings")
async def update_settings_endpoint(data: SettingsUpdateRequest):
    if data.resonance_threshold is not None:
        graph_instance.resonance_threshold = data.resonance_threshold
    if data.decay_rate is not None:
        graph_instance.decay_rate = data.decay_rate
    return {
        "status": "success",
        "message": "Settings updated successfully.",
        "resonance_threshold": graph_instance.resonance_threshold,
        "decay_rate": graph_instance.decay_rate
    }

class GravityUpdateRequest(BaseModel):
    node_id: str
    mass: float

@router.get("/gravity")
async def get_gravity_endpoint():
    if len(graph_instance.nx_graph) == 0:
        return {"planets": []}
        
    try:
        import networkx as nx
        pr = nx.pagerank(graph_instance.nx_graph, weight='weight')
    except Exception:
        pr = {nid: 1.0 for nid in graph_instance.nx_graph.nodes}
        
    sorted_nodes = sorted(pr.items(), key=lambda x: x[1], reverse=True)
    
    planets = []
    for nid, gravity in sorted_nodes[:10]:
        orbiters = list(graph_instance.nx_graph.neighbors(nid))
        mass = node_metrics.get(nid, {}).get("confidence", 0.8) if nid in node_metrics else 0.8
        planets.append({
            "id": nid,
            "gravity": gravity,
            "mass": mass,
            "orbiters": orbiters
        })
        
    return {"planets": planets}

@router.post("/gravity")
async def update_gravity_endpoint(data: GravityUpdateRequest):
    if data.node_id not in graph_instance.nodes:
        raise HTTPException(status_code=404, detail="Node not found")
        
    if data.node_id not in node_metrics:
        node_metrics[data.node_id] = {"confidence": 0.8, "plateau_factor": 0.0, "is_grounded": False, "help_chain": False}
        
    node_metrics[data.node_id]["confidence"] = data.mass
    
    # NEW: Dynamically promote/demote nodes to Reality Anchors based on massive gravity
    if data.mass >= 0.95:
        node_metrics[data.node_id]["is_grounded"] = True
    else:
        node_metrics[data.node_id]["is_grounded"] = False
    
    m = node_metrics[data.node_id]
    emb = graph_instance.nodes[data.node_id].detach()
    save_node(data.node_id, emb, 0.0, m["confidence"], m["plateau_factor"], m["is_grounded"], m["help_chain"], get_node_text(data.node_id))
    
    return {"status": "success", "node_id": data.node_id, "new_mass": data.mass, "is_anchor": m["is_grounded"]}

@router.post("/compress")
async def compress_graph_endpoint():
    # Topological Compression (MVC)
    import networkx as nx
    
    if len(graph_instance.nx_graph) < 3:
        return {"status": "success", "archived_nodes": [], "message": "Graph too small to compress."}
        
    # Get base centrality
    try:
        base_pr = nx.pagerank(graph_instance.nx_graph, weight='weight')
    except Exception:
        base_pr = {nid: 1.0 for nid in graph_instance.nx_graph.nodes}
        
    top_planets = [x[0] for x in sorted(base_pr.items(), key=lambda item: item[1], reverse=True)[:3]]
    
    archived = []
    
    # Iterate over potential plateau nodes
    nodes_to_check = list(graph_instance.nx_graph.nodes)
    for nid in nodes_to_check:
        if nid in top_planets:
            continue
            
        m = node_metrics.get(nid, {})
        plateau = m.get("plateau_factor", 0.0)
        
        # Heuristic: Check if node is saturated or irrelevant
        if plateau > 0.8 or base_pr.get(nid, 0) < 0.01:
            # Test removal
            temp_g = graph_instance.nx_graph.copy()
            temp_g.remove_node(nid)
            try:
                new_pr = nx.pagerank(temp_g, weight='weight')
            except Exception:
                continue
                
            # Check if top planets maintain their relative mass within 5% tolerance
            coherence_loss = 0.0
            for p in top_planets:
                if p in new_pr:
                    diff = abs(new_pr[p] - base_pr[p])
                    coherence_loss += diff
                    
            if coherence_loss < 0.05:
                # Compression successful! Node is redundant.
                archived.append(nid)
                
                safe_id = graph_instance._safe_id(nid)
                emb = graph_instance.nodes[safe_id].detach() if safe_id in graph_instance.nodes else text_to_embedding(get_node_text(nid))
                save_node(nid, emb, 0.0, m.get("confidence", 0.8), plateau, m.get("is_grounded", False), m.get("help_chain", False), get_node_text(nid), is_archived=True)
                
                graph_instance.remove_node(nid)
                if nid in node_metrics:
                    del node_metrics[nid]
                    
    # Generate snapshot commit when nodes are compressed so the exact state is versioned/reconstructible
    commit_hash = None
    if archived:
        from lgnn.database import create_snapshot
        commit_description = f"System compression cycle: Archived {len(archived)} redundant concepts ({', '.join(archived[:3])})"
        commit_hash = create_snapshot(commit_description, 1.0 - (coherence_loss if 'coherence_loss' in locals() else 0.0))
        
    return {
        "status": "success",
        "archived_nodes": archived,
        "commit_hash": commit_hash,
        "message": f"Topologically compressed {len(archived)} redundant concept(s) into the Subconscious Archive. Snapshot created: {commit_hash or 'None'}"
    }

@router.post("/ingest-multimodal")
async def ingest_multimodal_endpoint(data: dict):
    from lgnn.sensors import SensorArray
    import base64
    import os
    
    file_path = data.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}
        
    sensors = SensorArray()
    chunks = []
    
    if file_path.lower().endswith('.pdf'):
        chunks = sensors.parse_pdf(file_path)
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        with open(file_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode('utf-8')
        vision_desc = sensors._call_ollama(
            model=sensors.vision_model,
            prompt="Analyze this image deeply for the neural graph. Extract context, objects, text, and meaning.",
            images=[b64_img]
        )
        chunks.append({"type": "visual_description", "content": vision_desc, "metadata": file_path})
    elif file_path.lower().endswith(('.mp3', '.wav', '.m4a')):
        chunks = sensors.listen_to_audio(file_path)
    elif file_path.lower().endswith(('.obj', '.stl')):
        chunks = sensors.perceive_spatial_geometry(file_path)
    else:
        return {"status": "error", "message": "Unsupported file format for sensors."}
        
    # Process all chunks through the standard evolution pipeline
    processed_ids = []
    for chunk in chunks:
        # Check for errors in chunk ingestion
        if chunk.get("type") == "error":
            return {"status": "error", "message": chunk.get("content")}
            
        chunk_text = f"[{chunk['type'].upper()} | {chunk['metadata']}] {chunk['content']}"
        req_data = EvolveTextRequest(text=chunk_text)
        await evolve_text_endpoint(req_data)
        processed_ids.append(chunk_text[:30] + "...")
        
    return {"status": "success", "chunks_processed": len(chunks), "previews": processed_ids}

import base64

class SubgraphSyncRequest(BaseModel):
    client_id: str
    nodes: Dict[str, str] # node_id -> base64 tensor

@router.get("/distributed/export")
async def export_subgraph_endpoint(limit: int = 50):
    """
    Exports a lightweight subgraph bundle for mobile/edge devices.
    Edge devices can run the ODE locally to offload compute.
    """
    import random
    node_ids = list(graph_instance.nodes.keys())
    if not node_ids:
        return {"nodes": {}}
        
    # Select a random subset of nodes (or prioritize dormant ones)
    selected = random.sample(node_ids, min(limit, len(node_ids)))
    
    export_nodes = {}
    for nid in selected:
        tensor = graph_instance.nodes[nid]
        b64_data = base64.b64encode(tensor.detach().cpu().numpy().astype("float32").tobytes()).decode("ascii")
        export_nodes[nid] = {
            "tensor_b64": b64_data,
            "text": get_node_text(nid)
        }
        
    return {"status": "success", "nodes": export_nodes}

@router.post("/distributed/sync")
async def sync_subgraph_endpoint(data: SubgraphSyncRequest):
    """
    Receives evolved latent states from edge devices and merges them
    into the Mothership topology via Exponential Moving Average (EMA).
    """
    import numpy as np
    
    alpha = 0.1 # Blending factor (trust the Mothership more than the edge device)
    synced_count = 0
    
    for nid, b64_str in data.nodes.items():
        if nid in graph_instance.nodes:
            try:
                raw_bytes = base64.b64decode(b64_str)
                arr = np.frombuffer(raw_bytes, dtype=np.float32)
                if len(arr) != hidden_dim:
                    continue
                    
                edge_tensor = torch.tensor(arr, device=graph_instance.nodes[nid].device)
                
                # Merge logic (EMA)
                current_tensor = graph_instance.nodes[nid].detach()
                merged_tensor = (1.0 - alpha) * current_tensor + alpha * edge_tensor
                
                # Update Memory
                graph_instance.nodes[nid].data.copy_(merged_tensor)
                
                # Update SQLite
                m = node_metrics.get(nid, {"confidence": 0.8, "plateau_factor": 0.0, "is_grounded": False, "help_chain": False})
                mean_act = float(merged_tensor.mean().detach().cpu())
                save_node(nid, merged_tensor, mean_act, m["confidence"], m["plateau_factor"], m["is_grounded"], m["help_chain"], get_node_text(nid))
                
                synced_count += 1
            except Exception as e:
                logger.error(f"[Distributed] Failed to sync node {nid}: {e}")
                
    # Re-evaluate edges after sync
    if synced_count > 0:
        graph_instance.evolve_topology(compute_time=0.1) # Fast stabilization
        
    return {"status": "success", "synced_nodes": synced_count, "message": "Edge compute successfully merged into Prime topology."}

class SnapshotCreateRequest(BaseModel):
    description: str

class SnapshotCheckoutRequest(BaseModel):
    commit_hash: str

@router.post("/snapshot/create")
async def api_create_snapshot(data: SnapshotCreateRequest):
    """
    Saves a Git-like snapshot of the current active graph state.
    """
    from lgnn.database import create_snapshot
    from lgnn.coherence_checker import evaluate_graph_coherence
    
    # 1. Get current coherence score
    node_ids = list(graph_instance.nodes.keys())
    coherence_score = 1.0
    if node_ids:
        coh_res = evaluate_graph_coherence(node_ids[:5], hidden_dim=hidden_dim) # Sample evaluate first few nodes
        coherence_score = coh_res.get("coherence_score", 1.0)
        
    # 2. Create snapshot
    commit_hash = create_snapshot(data.description, coherence_score)
    return {"status": "success", "commit_hash": commit_hash, "coherence_score": coherence_score}

@router.post("/snapshot/checkout")
async def api_checkout_snapshot(data: SnapshotCheckoutRequest):
    """
    Restores the graph state to a previous snapshot commit hash.
    """
    from lgnn.database import checkout_snapshot
    success, msg = checkout_snapshot(data.commit_hash, dim=hidden_dim)
    if not success:
        raise HTTPException(status_code=404, detail=msg)
        
    # Re-sync in-memory state with DB
    load_all_from_db()
    return {"status": "success", "message": msg}

@router.get("/snapshot/history")
async def api_snapshot_history():
    """
    Lists all available snapshot commits in the topology history.
    """
    from lgnn.database import get_snapshot_history
    history = get_snapshot_history()
    return {"status": "success", "history": history}

