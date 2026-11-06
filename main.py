from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from engine import new_game, public_state, move_unit, attack_unit, recruit, end_turn, OPERATIONS
from copy import deepcopy

app=FastAPI(title="Iron Frontier API",version="2.0.0",description="Turn-based strategy game engine")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
GAMES={}
class NewGame(BaseModel): operation_id:str="frontier"
class MoveRequest(BaseModel): unit_id:str; destination_id:str
class AttackRequest(BaseModel): unit_id:str; target_id:str
class RecruitRequest(BaseModel): unit_type:str; city_id:str
class RestoreRequest(BaseModel): state:dict=Field(...)
def get_game(game_id):
    if game_id not in GAMES: raise HTTPException(404,"Game session not found. Create a new game or restore a saved game.")
    return GAMES[game_id]
def response(state): return {"game":public_state(state)}
def run_action(game_id,fn,*args):
    state=get_game(game_id)
    try: fn(state,*args)
    except ValueError as e: raise HTTPException(400,str(e))
    return response(state)
@app.get("/health")
def health(): return {"status":"ok","service":"iron-frontier-api","version":"2.0.0"}
@app.get("/operations")
def operations(): return {"operations":OPERATIONS}
@app.post("/games")
def create_game(body:NewGame):
    state=new_game(body.operation_id);GAMES[state["id"]]=state;return response(state)
@app.get("/games/{game_id}")
def read_game(game_id:str): return response(get_game(game_id))
@app.post("/games/restore")
def restore_game(body:RestoreRequest):
    state=deepcopy(body.state)
    required={"id","tiles","units","turn","side","credits","operationId"}
    if not required.issubset(state): raise HTTPException(400,"Save file is incomplete or invalid.")
    GAMES[state["id"]]=state;return response(state)
@app.post("/games/{game_id}/move")
def move(game_id:str,body:MoveRequest): return run_action(game_id,move_unit,body.unit_id,body.destination_id)
@app.post("/games/{game_id}/attack")
def attack(game_id:str,body:AttackRequest): return run_action(game_id,attack_unit,body.unit_id,body.target_id)
@app.post("/games/{game_id}/recruit")
def hire(game_id:str,body:RecruitRequest): return run_action(game_id,recruit,body.unit_type,body.city_id)
@app.post("/games/{game_id}/end-turn")
def finish_turn(game_id:str): return run_action(game_id,end_turn)
