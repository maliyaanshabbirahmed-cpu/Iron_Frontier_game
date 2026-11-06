from __future__ import annotations
from copy import deepcopy
from collections import deque
import random, uuid

UNIT_TYPES = {
    "infantry": {"name":"Infantry", "icon":"♟", "cost":75, "hp":80, "atk":20, "def":9, "range":1, "move":2, "upkeep":3},
    "tank": {"name":"Heavy tank", "icon":"▰", "cost":150, "hp":125, "atk":34, "def":17, "range":1, "move":3, "upkeep":7},
    "artillery": {"name":"Field artillery", "icon":"◉", "cost":125, "hp":70, "atk":29, "def":6, "range":3, "move":1, "upkeep":5},
    "recon": {"name":"Recon vehicle", "icon":"◆", "cost":105, "hp":75, "atk":17, "def":8, "range":1, "move":4, "upkeep":4},
}
TERRAIN = {
    "plain":{"label":"Plains", "def":0, "cost":1}, "forest":{"label":"Forest", "def":5, "cost":2},
    "mountain":{"label":"Mountain", "def":9, "cost":2}, "desert":{"label":"Desert", "def":-2, "cost":1},
    "city":{"label":"City", "def":4, "cost":1}, "river":{"label":"River", "def":2, "cost":2},
}
# Hand-authored fictional theatre. Coordinates form a 7x5 tactical grid.
_RAW = [
("northport","Northport",0,0,"city","player"),("pine_ridge","Pine Ridge",1,0,"forest","player"),("high_pass","High Pass",2,0,"mountain","neutral"),("red_farm","Red Farm",3,0,"plain","enemy"),("eastwatch","Eastwatch",4,0,"city","enemy"),("cliffside","Cliffside",5,0,"mountain","enemy"),("radar_hill","Radar Hill",6,0,"mountain","enemy"),
("west_farm","West Farm",0,1,"plain","player"),("old_forest","Old Forest",1,1,"forest","player"),("iron_hills","Iron Hills",2,1,"mountain","neutral"),("crossroads","Crossroads",3,1,"plain","enemy"),("sunfield","Sunfield",4,1,"plain","enemy"),("dry_creek","Dry Creek",5,1,"river","enemy"),("north_battery","North Battery",6,1,"plain","enemy"),
("harbor","Harbor",0,2,"city","player"),("riverbend","Riverbend",1,2,"river","neutral"),("central_city","Central City",2,2,"city","neutral"),("dust_bowl","Dust Bowl",3,2,"desert","enemy"),("supply_depot","Supply Depot",4,2,"city","enemy"),("south_gate","South Gate",5,2,"city","enemy"),("coastline","Coastline",6,2,"plain","enemy"),
("south_farm","South Farm",0,3,"plain","player"),("marshland","Marshland",1,3,"forest","neutral"),("granite","Granite",2,3,"mountain","neutral"),("dry_river","Dry River",3,3,"desert","enemy"),("old_quarry","Old Quarry",4,3,"mountain","enemy"),("port_road","Port Road",5,3,"plain","enemy"),("southern_coast","Southern Coast",6,3,"plain","enemy"),
("western_outpost","Western Outpost",0,4,"plain","player"),("lowlands","Lowlands",1,4,"plain","neutral"),("ridge","Ridge",2,4,"mountain","neutral"),("farmland","Farmland",3,4,"plain","neutral"),("rail_yard","Rail Yard",4,4,"city","enemy"),("southern_pass","Southern Pass",5,4,"mountain","enemy"),("delta","Delta",6,4,"river","enemy"),
]
CITIES = {"northport","eastwatch","harbor","central_city","supply_depot","south_gate","rail_yard"}
OPERATIONS = [
 {"id":"frontier","name":"Operation Iron Line","subtitle":"Secure the central corridor","description":"Capture Central City and control at least three cities.","target":"central_city","cities":3,"reward":220,"enemy_bonus":0},
 {"id":"harbor","name":"Operation Breakwater","subtitle":"Cut off the coastal supply route","description":"Capture Eastwatch and South Gate while holding four cities.","target":"eastwatch","cities":4,"reward":300,"enemy_bonus":1},
 {"id":"last_stand","name":"Operation Last Stand","subtitle":"Remove the hostile command network","description":"Capture all hostile cities in the theatre.","target":"all","cities":7,"reward":420,"enemy_bonus":2},
]

def _tile_rows():
    return [dict(id=i,name=n,x=x,y=y,terrain=t,owner=o,city=i in CITIES) for i,n,x,y,t,o in _RAW]

def new_game(operation_id="frontier"):
    op = next((x for x in OPERATIONS if x["id"]==operation_id), OPERATIONS[0])
    tiles = _tile_rows()
    if operation_id == "harbor":
        next(t for t in tiles if t["id"]=="central_city")["owner"]="enemy"
    if operation_id == "last_stand":
        for t in tiles:
            if t["owner"]=="neutral": t["owner"]="enemy"
    units = [
      {"id":"A-01","owner":"player","type":"infantry","tile":"northport","hp":80,"acted":False,"veteran":0},
      {"id":"A-02","owner":"player","type":"tank","tile":"west_farm","hp":125,"acted":False,"veteran":0},
      {"id":"A-03","owner":"player","type":"artillery","tile":"harbor","hp":70,"acted":False,"veteran":0},
      {"id":"A-04","owner":"player","type":"recon","tile":"south_farm","hp":75,"acted":False,"veteran":0},
      {"id":"E-01","owner":"enemy","type":"infantry","tile":"eastwatch","hp":80,"acted":False,"veteran":0},
      {"id":"E-02","owner":"enemy","type":"tank","tile":"sunfield","hp":125,"acted":False,"veteran":0},
      {"id":"E-03","owner":"enemy","type":"artillery","tile":"south_gate","hp":70,"acted":False,"veteran":0},
      {"id":"E-04","owner":"enemy","type":"infantry","tile":"red_farm","hp":80,"acted":False,"veteran":0},
      {"id":"E-05","owner":"enemy","type":"recon","tile":"rail_yard","hp":75,"acted":False,"veteran":0},
    ]
    if op["enemy_bonus"]>=1: units.append({"id":"E-06","owner":"enemy","type":"infantry","tile":"north_battery","hp":80,"acted":False,"veteran":0})
    if op["enemy_bonus"]>=2: units.append({"id":"E-07","owner":"enemy","type":"tank","tile":"port_road","hp":125,"acted":False,"veteran":0})
    return {"id":str(uuid.uuid4()),"tiles":tiles,"units":units,"turn":1,"side":"player","credits":360,"score":0,"selected":None,"log":["Command established. Secure the corridor and protect your supply lines."],"operationId":operation_id,"ended":False,"result":None,"weather":"Clear","difficulty":"Standard"}

def tile(state, tile_id):
    return next((t for t in state["tiles"] if t["id"]==tile_id),None)
def unit_at(state, tile_id):
    return next((u for u in state["units"] if u["tile"]==tile_id),None)
def log(state, message): state["log"]=( [message]+state.get("log",[]) )[:10]
def distance(a,b): return abs(a["x"]-b["x"])+abs(a["y"]-b["y"])
def _path_cost(state, unit, destination_id):
    start=tile(state,unit["tile"]); goal=tile(state,destination_id)
    if not start or not goal: return None
    q=deque([(start["id"],0)]); seen={start["id"]:0}
    while q:
        current,cost=q.popleft()
        if current==goal["id"]: return cost
        cur=tile(state,current)
        for nxt in state["tiles"]:
            blocked_owner = "enemy" if unit["owner"] == "player" else None
            is_goal = nxt["id"] == goal["id"]
            if distance(cur,nxt)!=1 or (blocked_owner and nxt["owner"]==blocked_owner and not is_goal) or (unit_at(state,nxt["id"]) and not is_goal): continue
            step=TERRAIN[nxt["terrain"]]["cost"]
            new=cost+step
            if new<=UNIT_TYPES[unit["type"]]["move"] and new<seen.get(nxt["id"],999):
                seen[nxt["id"]]=new;q.append((nxt["id"],new))
    return seen.get(goal["id"])
def legal_moves(state, unit):
    if unit["owner"]!="player" or unit["acted"] or state["side"]!="player": return []
    out=[]
    for t in state["tiles"]:
        if t["id"]==unit["tile"] or (t["owner"]=="enemy" and not t["city"]) or unit_at(state,t["id"]): continue
        cost=_path_cost(state,unit,t["id"])
        if cost is not None and cost<=UNIT_TYPES[unit["type"]]["move"]: out.append(t["id"])
    return out
def legal_attacks(state, unit):
    if unit["owner"]!="player" or unit["acted"] or state["side"]!="player": return []
    origin=tile(state,unit["tile"]); r=UNIT_TYPES[unit["type"]]["range"]
    return [u["tile"] for u in state["units"] if u["owner"]=="enemy" and distance(origin,tile(state,u["tile"]))<=r]
def _finish(state):
    op=next(x for x in OPERATIONS if x["id"]==state["operationId"])
    held=sum(t["city"] and t["owner"]=="player" for t in state["tiles"])
    hostile_cities=sum(t["city"] and t["owner"]=="enemy" for t in state["tiles"])
    target=tile(state,op["target"]) if op["target"]!="all" else None
    won=(hostile_cities==0 if op["id"]=="last_stand" else bool(target and target["owner"]=="player") and held>=op["cities"])
    if won and not state["ended"]:
        state["ended"]=True;state["result"]="victory";state["credits"]+=op["reward"];log(state,f"Operation complete. {op['reward']} requisition credits awarded.")
    elif not any(u["owner"]=="player" for u in state["units"]):
        state["ended"]=True;state["result"]="defeat";log(state,"All allied units have been lost. Operation failed.")

def move_unit(state, unit_id, destination_id):
    if state["ended"] or state["side"]!="player": raise ValueError("It is not your command phase.")
    u=next((u for u in state["units"] if u["id"]==unit_id and u["owner"]=="player"),None)
    if not u: raise ValueError("Select a valid allied unit.")
    if destination_id not in legal_moves(state,u): raise ValueError("That destination is not reachable this turn.")
    dest=tile(state,destination_id);u["tile"]=destination_id;u["acted"]=True
    if dest["city"] and dest["owner"]!="player":
        dest["owner"]="player";state["score"]+=60;log(state,f"{dest['name']} captured. Supply income increased.")
    else: log(state,f"{UNIT_TYPES[u['type']]['name']} redeployed to {dest['name']}.")
    state["selected"]=None;_finish(state);return state

def attack_unit(state, unit_id, target_id):
    if state["ended"] or state["side"]!="player": raise ValueError("It is not your command phase.")
    a=next((u for u in state["units"] if u["id"]==unit_id and u["owner"]=="player"),None);d=unit_at(state,target_id)
    if not a or not d or target_id not in legal_attacks(state,a): raise ValueError("Target is not in attack range.")
    terrain=tile(state,target_id)["terrain"];spec=UNIT_TYPES[a["type"]];ds=UNIT_TYPES[d["type"]]
    bonus=4 if a["type"]=="tank" and d["type"] in ("infantry","artillery") else 3 if a["type"]=="artillery" and terrain=="plain" else 0
    damage=max(8,round(spec["atk"]+bonus+random.randint(-3,4)-(ds["def"]+TERRAIN[terrain]["def"])*.48))
    d["hp"]-=damage;a["acted"]=True
    msg=f"{spec['name']} inflicted {damage} damage."
    if d["hp"]<=0:
        state["units"].remove(d);a["veteran"]+=1;state["score"]+=45;state["credits"]+=20;msg+=f" {ds['name']} destroyed (+20 credits)."
    else:
        counter=max(0,round(ds["atk"]*.22-(spec["def"]*.12))) if ds["range"]>=distance(tile(state,a["tile"]),tile(state,d["tile"])) else 0
        if counter:
            a["hp"]-=counter;msg+=f" Return fire: {counter} damage."
            if a["hp"]<=0: state["units"].remove(a);msg+=" Allied unit destroyed."
    state["selected"]=None;log(state,msg);_finish(state);return state

def recruit(state, unit_type, city_id):
    if state["ended"] or state["side"]!="player": raise ValueError("Recruitment is unavailable now.")
    if unit_type not in UNIT_TYPES: raise ValueError("Unknown unit type.")
    c=tile(state,city_id);spec=UNIT_TYPES[unit_type]
    if not c or not c["city"] or c["owner"]!="player": raise ValueError("Recruitment requires a friendly city.")
    if unit_at(state,city_id): raise ValueError("That city already has a unit stationed there.")
    if state["credits"]<spec["cost"]: raise ValueError("Insufficient requisition credits.")
    state["credits"]-=spec["cost"];state["units"].append({"id":f"A-{uuid.uuid4().hex[:4].upper()}","owner":"player","type":unit_type,"tile":city_id,"hp":spec["hp"],"acted":True,"veteran":0})
    log(state,f"{spec['name']} recruited at {c['name']}. It deploys next turn.");return state

def _enemy_turn(state):
    enemies=[u for u in state["units"] if u["owner"]=="enemy"]
    for enemy in enemies:
        if enemy not in state["units"]: continue
        spec=UNIT_TYPES[enemy["type"]];origin=tile(state,enemy["tile"])
        targets=[u for u in state["units"] if u["owner"]=="player" and distance(origin,tile(state,u["tile"]))<=spec["range"]]
        if targets:
            target=min(targets,key=lambda u:u["hp"]);ts=UNIT_TYPES[target["type"]]
            dmg=max(7,round(spec["atk"]*.72+random.randint(-2,3)-(ts["def"]+TERRAIN[tile(state,target["tile"])["terrain"]]["def"])*.3))
            target["hp"]-=dmg;log(state,f"Hostile {spec['name']} hit allied {ts['name']} for {dmg}.")
            if target["hp"]<=0: state["units"].remove(target);log(state,f"Allied {ts['name']} unit destroyed.")
            continue
        # Move one reachable step toward an allied city or unit; prefer city captures.
        candidates=[]
        for t in state["tiles"]:
            if t["owner"]=="enemy" or unit_at(state,t["id"]): continue
            cost=_path_cost(state,enemy,t["id"])
            if cost is not None and cost<=spec["move"]:
                nearby=min((distance(t,tile(state,u["tile"])) for u in state["units"] if u["owner"]=="player"),default=99)
                priority=(0 if t["city"] and t["owner"]=="player" else 1, nearby, cost)
                candidates.append((priority,t))
        if candidates:
            candidates.sort(key=lambda z:z[0]);dest=candidates[0][1]
            # Avoid aimless lateral movement: only move if it approaches a player unit or city.
            enemy["tile"]=dest["id"]
            if dest["city"] and dest["owner"]!="enemy": dest["owner"]="enemy";log(state,f"Hostile forces captured {dest['name']}.")
    for u in state["units"]:
        if u["owner"]=="enemy": u["acted"]=False

def end_turn(state):
    if state["ended"] or state["side"]!="player": raise ValueError("Cannot end the turn now.")
    state["side"]="enemy";_enemy_turn(state);state["turn"]+=1;state["side"]="player"
    for u in state["units"]:
        if u["owner"]=="player": u["acted"]=False
    held=sum(t["city"] and t["owner"]=="player" for t in state["tiles"])
    income=held*40
    state["credits"]+=income
    log(state,f"Turn {state['turn']} begins. City income: +{income} credits.")
    _finish(state);return state

def public_state(state):
    result=deepcopy(state)
    result["unit_types"]=UNIT_TYPES;result["terrain_types"]=TERRAIN;result["operations"]=OPERATIONS
    result["legal_moves"]={u["id"]:legal_moves(state,u) for u in state["units"] if u["owner"]=="player"}
    result["legal_attacks"]={u["id"]:legal_attacks(state,u) for u in state["units"] if u["owner"]=="player"}
    result["stats"]={"allied_units":sum(u["owner"]=="player" for u in state["units"]),"enemy_units":sum(u["owner"]=="enemy" for u in state["units"]),"cities_held":sum(t["city"] and t["owner"]=="player" for t in state["tiles"]),"enemy_cities":sum(t["city"] and t["owner"]=="enemy" for t in state["tiles"]),"income":sum(t["city"] and t["owner"]=="player" for t in state["tiles"])*40}
    return result
