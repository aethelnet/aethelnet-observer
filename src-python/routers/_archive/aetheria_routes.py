from fastapi import APIRouter
from pydantic import BaseModel
import logging

logger = logging.getLogger("Aetheria.Router")

class CombatRequest(BaseModel):
    attacker_id: str
    defender_id: str
    skill_node_id: str = None

class SpliceRequest(BaseModel):
    player_id: str
    component_id: str

class SpawnRequest(BaseModel):
    manual_node_id: str = None

class SeverRequest(BaseModel):
    boss_id: str
    component_id: str

class FusionRequest(BaseModel):
    node_a_id: str
    node_b_id: str

def register_aetheria_routes(router: APIRouter):
    @router.post("/aetheria/combat")
    def trigger_combat(req: CombatRequest):
        from lgnn.aetheria_engine import resolve_combat
        try:
            res = resolve_combat(req.attacker_id, req.defender_id, req.skill_node_id)
            return res
        except Exception as e:
            logger.error(f"Combat error: {e}")
            return {"status": "error", "message": str(e)}

    @router.post("/aetheria/splice")
    def trigger_splice(req: SpliceRequest):
        from lgnn.aetheria_engine import splice_component
        try:
            res = splice_component(req.player_id, req.component_id)
            return res
        except Exception as e:
            logger.error(f"Splice error: {e}")
            return {"status": "error", "message": str(e)}

    @router.post("/aetheria/sever")
    def trigger_sever(req: SeverRequest):
        from lgnn.aetheria_engine import sever_component
        try:
            res = sever_component(req.boss_id, req.component_id)
            return res
        except Exception as e:
            logger.error(f"Sever error: {e}")
            return {"status": "error", "message": str(e)}

    @router.post("/aetheria/resolve_fusion")
    async def trigger_fusion(req: FusionRequest):
        from lgnn.aetheria_engine import resolve_fusion
        from lgnn.websocket import manager
        import json
        try:
            res = resolve_fusion(req.node_a_id, req.node_b_id)
            if res.get("status") == "success":
                await manager.broadcast(json.dumps({
                    "type": "global_event",
                    "event": "AETHERIA_FUSION",
                    "fused_id": res["fused_id"],
                    "node_a": req.node_a_id,
                    "node_b": req.node_b_id
                }))
            return res
        except Exception as e:
            logger.error(f"Fusion error: {e}")
            return {"status": "error", "message": str(e)}

    @router.post("/aetheria/spawn")
    async def spawn_monster(req: SpawnRequest):
        from services.spider_aetheria import AetheriaSpider
        from lgnn.websocket import manager
        import json
        try:
            spider = AetheriaSpider()
            if req.manual_node_id:
                # Spawn at specific node
                nodes = [(req.manual_node_id, "Manual anomaly generation", 0.8)]
            else:
                nodes = spider.fetch_dissonant_nodes()
                if not nodes:
                    nodes = [("random_void", "The empty space between thoughts.", 0.6)]
            
            spawned = []
            for node in nodes:
                monster_id = spider.spawn_monsters_at_node(node)
                if monster_id:
                    spawned.append(monster_id)
            
            # Broadcast the event to shake the frontend
            await manager.broadcast(json.dumps({
                "type": "AETHERIA_SPAWN",
                "monster_ids": spawned
            }))
            
            return {"status": "success", "spawned": spawned}
        except Exception as e:
            logger.error(f"Spawn error: {e}")
            return {"status": "error", "message": str(e)}

    @router.post("/aetheria/arxiv_scan")
    async def arxiv_scan():
        from services.spider_arxiv import ArxivSpider
        from lgnn.websocket import manager
        import json
        try:
            spider = ArxivSpider()
            new_concept_ids = spider.run_scan()
            
            if new_concept_ids:
                await manager.broadcast(json.dumps({
                    "type": "global_event",
                    "event": "ARXIV_INSIGHT",
                    "nodes": new_concept_ids
                }))
            
            return {"status": "success", "processed": len(new_concept_ids), "nodes": new_concept_ids}
        except Exception as e:
            logger.error(f"Arxiv scan error: {e}")
            return {"status": "error", "message": str(e)}
