"""Juego de ajedrez para el asistente de Elite Flower.

El tablero y la IA corren en el navegador (JavaScript), así que no gastan
recursos del servidor ni llamadas a Gemini. Las reglas las maneja chess.js.
"""
import streamlit.components.v1 as components

CHESS_HTML = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}
html,body{margin:0;background:transparent;color:#eef2ff;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:560px;margin:0 auto;padding:6px}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;justify-content:center;margin-bottom:8px}
label{font-size:11px;color:#929bb0;text-transform:uppercase;letter-spacing:1px;
  display:flex;flex-direction:column;gap:4px}
select,button{background:#0b1018;color:#00ffd5;border:1px solid rgba(0,255,213,.35);
  border-radius:9px;padding:8px 12px;font-size:14px;cursor:pointer}
button:hover,select:hover{border-color:#00ffd5;box-shadow:0 0 12px rgba(0,255,213,.2)}
button:disabled{opacity:.5;cursor:default}
.status{text-align:center;font-weight:700;margin:8px 0 10px;min-height:24px;font-size:16px}
#board{display:grid;grid-template-columns:repeat(8,1fr);width:100%;aspect-ratio:1/1;
  border:3px solid #ff4fc3;border-radius:6px;overflow:hidden;
  box-shadow:0 0 25px rgba(255,79,195,.28);user-select:none;-webkit-user-select:none}
.sq{position:relative;display:flex;align-items:center;justify-content:center;
  cursor:pointer;font-size:var(--fs,40px);line-height:1;overflow:hidden}
.light{background-color:#f3e3ea}
.dark{background-color:#b86aa0}
.last{background-image:linear-gradient(rgba(255,235,59,.5),rgba(255,235,59,.5))}
.chk{background-image:radial-gradient(circle,rgba(255,0,0,.85) 0%,rgba(255,0,0,0) 72%)}
.sel{box-shadow:inset 0 0 0 4px #ffd54a}
.dot::after{content:"";position:absolute;width:28%;height:28%;border-radius:50%;background:rgba(0,0,0,.30)}
.cap::after{content:"";position:absolute;inset:5%;border-radius:50%;border:5px solid rgba(0,0,0,.30)}
.w{color:#fff;text-shadow:0 0 2px #000,0 0 2px #000,0 1px 3px #000}
.b{color:#141414;text-shadow:0 0 1px rgba(255,255,255,.55)}
.coord{position:absolute;font-size:10px;font-weight:700;opacity:.8;color:#4a2a42;pointer-events:none;
  font-family:system-ui,sans-serif;text-shadow:none}
.rank{top:2px;left:3px}
.file{bottom:1px;right:3px}
.moves{margin-top:10px;max-height:84px;overflow:auto;font-size:13px;color:#929bb0;
  background:#0b0f17;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:8px 10px;line-height:1.6}
.err{color:#ff7a90;text-align:center;padding:30px 10px}
</style>
</head>
<body>
<div class="wrap">
  <div class="controls">
    <label>Dificultad
      <select id="level">
        <option value="facil">Fácil</option>
        <option value="intermedio" selected>Intermedio</option>
        <option value="avanzado">Avanzado</option>
      </select>
    </label>
    <label>Juegas con
      <select id="color">
        <option value="w">Blancas</option>
        <option value="b">Negras</option>
      </select>
    </label>
    <button id="newBtn">Nueva partida</button>
    <button id="undoBtn">Deshacer</button>
  </div>
  <div class="status" id="status">Cargando…</div>
  <div id="board"></div>
  <div class="moves" id="moves">La partida aún no comienza.</div>
</div>

<script>
function loadScript(urls, done, fail){
  if(!urls.length){ fail(); return; }
  const s=document.createElement('script');
  s.src=urls[0];
  s.onload=done;
  s.onerror=()=>loadScript(urls.slice(1),done,fail);
  document.head.appendChild(s);
}
loadScript([
  'https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js',
  'https://cdn.jsdelivr.net/npm/chess.js@0.10.3/chess.min.js'
], start, function(){
  document.querySelector('.wrap').innerHTML =
    '<div class="err">No se pudo cargar el motor de ajedrez. Revisa tu conexión y recarga la página.</div>';
});

function start(){

// ==ENGINE_START==
const VAL={p:100,n:320,b:330,r:500,q:900,k:20000};
const PST={
p:[0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10, 5,5,10,25,25,10,5,5,
   0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5, 5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0],
n:[-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40, -30,0,10,15,15,10,0,-30, -30,5,15,20,20,15,5,-30,
   -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30, -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50],
b:[-20,-10,-10,-10,-10,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,10,10,5,0,-10, -10,5,5,10,10,5,5,-10,
   -10,0,10,10,10,10,0,-10, -10,10,10,10,10,10,10,-10, -10,5,0,0,0,0,5,-10, -20,-10,-10,-10,-10,-10,-10,-20],
r:[0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
   -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0],
q:[-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5,
   0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10, -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20],
k:[-30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30, -20,-30,-30,-40,-40,-30,-30,-20, -10,-20,-20,-20,-20,-20,-20,-10,
   20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20]
};
const MATE=100000;
let game=new Chess();
let deadline=0, aborted=false, nodes=0;

function mv(m){ return {from:m.from,to:m.to,promotion:m.promotion||undefined}; }
function tick(){ if((++nodes&127)===0 && Date.now()>deadline) aborted=true; }

// Evaluación desde el punto de vista de quien mueve.
function evalSide(){
  const b=game.board(); let s=0;
  for(let r=0;r<8;r++){
    for(let c=0;c<8;c++){
      const p=b[r][c]; if(!p) continue;
      const idx=p.color==='w' ? r*8+c : (7-r)*8+c;
      const v=VAL[p.type]+PST[p.type][idx];
      s+= p.color==='w' ? v : -v;
    }
  }
  return game.turn()==='w' ? s : -s;
}

function order(moves){
  for(const m of moves){
    m._s=(m.captured ? 10*VAL[m.captured]-VAL[m.piece] : 0)+(m.promotion?800:0)+Math.random()*0.5;
  }
  moves.sort((a,b)=>b._s-a._s);
  return moves;
}

function quiesce(alpha,beta,qd){
  tick(); if(aborted) return 0;
  const stand=evalSide();
  if(stand>=beta) return beta;
  if(alpha<stand) alpha=stand;
  if(qd>=4) return alpha;
  const caps=game.moves({verbose:true}).filter(m=>m.captured||m.promotion);
  order(caps);
  for(const m of caps){
    game.move(mv(m));
    const sc=-quiesce(-beta,-alpha,qd+1);
    game.undo();
    if(aborted) return 0;
    if(sc>=beta) return beta;
    if(sc>alpha) alpha=sc;
  }
  return alpha;
}

function negamax(depth,alpha,beta,ply,useQ){
  tick(); if(aborted) return 0;
  if(depth===0) return useQ ? quiesce(alpha,beta,0) : evalSide();
  const moves=game.moves({verbose:true});
  if(moves.length===0) return game.in_check() ? -MATE+ply : 0;
  order(moves);
  for(const m of moves){
    game.move(mv(m));
    const sc=-negamax(depth-1,-beta,-alpha,ply+1,useQ);
    game.undo();
    if(aborted) return 0;
    if(sc>=beta) return beta;
    if(sc>alpha) alpha=sc;
  }
  return alpha;
}

const LEVELS={
  facil:      {depth:1, time:600,  rand:0.30, useQ:false},
  intermedio: {depth:2, time:2000, rand:0,    useQ:true},
  avanzado:   {depth:4, time:3500, rand:0,    useQ:true}
};

function findBest(level){
  const cfg=LEVELS[level]||LEVELS.intermedio;
  const moves=order(game.moves({verbose:true}));
  if(!moves.length) return null;
  if(Math.random()<cfg.rand) return moves[Math.floor(Math.random()*moves.length)];
  let best=moves[0];
  deadline=Date.now()+cfg.time; aborted=false; nodes=0;
  for(let d=1; d<=cfg.depth; d++){
    let bestD=null, bestScore=-Infinity, alpha=-Infinity;
    for(const m of moves){
      game.move(mv(m));
      const sc=-negamax(d-1,-Infinity,-alpha,1,cfg.useQ);
      game.undo();
      if(aborted) break;
      if(sc>bestScore){ bestScore=sc; bestD=m; }
      if(sc>alpha) alpha=sc;
    }
    if(aborted) break;
    if(bestD){
      best=bestD;
      moves.splice(moves.indexOf(bestD),1);
      moves.unshift(bestD);
    }
  }
  return best;
}
// ==ENGINE_END==

// ---------- Interfaz ----------
const FILES='abcdefgh';
const GLYPH={k:'\u265A\uFE0E',q:'\u265B\uFE0E',r:'\u265C\uFE0E',b:'\u265D\uFE0E',n:'\u265E\uFE0E',p:'\u265F\uFE0E'};
let playerColor='w', thinking=false, selected=null, legal=[];
const boardEl=document.getElementById('board');
const statusEl=document.getElementById('status');
const movesEl=document.getElementById('moves');
const levelSel=document.getElementById('level');
const colorSel=document.getElementById('color');
const undoBtn=document.getElementById('undoBtn');

function sizeBoard(){
  const w=boardEl.getBoundingClientRect().width;
  boardEl.style.setProperty('--fs',(w/8*0.78)+'px');
}
window.addEventListener('resize',sizeBoard);

function statusText(){
  if(game.in_checkmate()) return game.turn()===playerColor ? '💀 Jaque mate. Ganó la IA' : '🎉 ¡Jaque mate! Ganaste';
  if(game.in_stalemate()) return '🤝 Tablas por rey ahogado';
  if(game.insufficient_material()) return '🤝 Tablas por material insuficiente';
  if(game.in_threefold_repetition()) return '🤝 Tablas por repetición';
  if(game.in_draw()) return '🤝 Tablas';
  if(thinking) return '🤔 La IA está pensando…';
  return (game.in_check() ? '⚠️ ¡Jaque! ' : '') + 'Tu turno';
}

function renderMoves(){
  const h=game.history();
  if(!h.length){ movesEl.textContent='La partida aún no comienza.'; return; }
  let out='';
  for(let i=0;i<h.length;i+=2){
    out+=(i/2+1)+'. '+h[i]+(h[i+1]?' '+h[i+1]:'')+'   ';
  }
  movesEl.textContent=out;
  movesEl.scrollTop=movesEl.scrollHeight;
}

function render(){
  boardEl.innerHTML='';
  const b=game.board();
  const hist=game.history({verbose:true});
  const last=hist.length?hist[hist.length-1]:null;
  let kingSq=null;
  if(game.in_check()){
    for(let r=0;r<8;r++)for(let c=0;c<8;c++){
      const p=b[r][c];
      if(p && p.type==='k' && p.color===game.turn()) kingSq=FILES[c]+(8-r);
    }
  }
  const idx=[0,1,2,3,4,5,6,7];
  const rows=playerColor==='w' ? idx : idx.slice().reverse();
  const cols=playerColor==='w' ? idx : idx.slice().reverse();
  rows.forEach((r,ri)=>{
    cols.forEach((c,ci)=>{
      const sq=FILES[c]+(8-r);
      const p=b[r][c];
      const d=document.createElement('div');
      let cls='sq '+(((r+c)%2===0)?'light':'dark');
      if(last && (last.from===sq||last.to===sq)) cls+=' last';
      if(sq===kingSq) cls+=' chk';
      if(sq===selected) cls+=' sel';
      const target=legal.find(m=>m.to===sq);
      if(target) cls+= p ? ' cap' : ' dot';
      d.className=cls;
      if(p){
        const span=document.createElement('span');
        span.className=p.color;
        span.textContent=GLYPH[p.type];
        d.appendChild(span);
      }
      if(ci===0){ const e=document.createElement('span'); e.className='coord rank'; e.textContent=8-r; d.appendChild(e); }
      if(ri===7){ const e=document.createElement('span'); e.className='coord file'; e.textContent=FILES[c]; d.appendChild(e); }
      d.addEventListener('click',()=>onSquare(sq));
      boardEl.appendChild(d);
    });
  });
  statusEl.textContent=statusText();
  undoBtn.disabled=thinking;
  renderMoves();
  sizeBoard();
}

function onSquare(sq){
  if(thinking||game.game_over()||game.turn()!==playerColor) return;
  const target=legal.find(m=>m.to===sq);
  if(selected && target){
    const o={from:selected,to:sq};
    if(legal.some(m=>m.to===sq && m.promotion)) o.promotion='q'; // se corona dama automáticamente
    game.move(o);
    selected=null; legal=[];
    afterPlayerMove();
    return;
  }
  const p=game.get(sq);
  if(p && p.color===playerColor){
    selected=sq; legal=game.moves({square:sq,verbose:true});
  } else { selected=null; legal=[]; }
  render();
}

function scheduleAI(){
  thinking=true; render();
  requestAnimationFrame(()=>setTimeout(aiMove,40));
}

function afterPlayerMove(){
  if(game.game_over()){ thinking=false; render(); return; }
  scheduleAI();
}

function aiMove(){
  if(!game.game_over()){
    const m=findBest(levelSel.value);
    if(m) game.move(mv(m));
  }
  thinking=false;
  render();
}

function newGame(){
  game=new Chess();
  selected=null; legal=[]; thinking=false;
  playerColor=colorSel.value;
  render();
  if(playerColor==='b') scheduleAI();
}

function undo(){
  if(thinking||game.history().length===0) return;
  do { game.undo(); } while(game.turn()!==playerColor && game.history().length>0);
  selected=null; legal=[];
  if(game.turn()!==playerColor && !game.game_over()) { scheduleAI(); return; }
  render();
}

document.getElementById('newBtn').addEventListener('click',newGame);
undoBtn.addEventListener('click',undo);
colorSel.addEventListener('change',newGame);
newGame();

} // fin start()
</script>
</body>
</html>
"""


def render_chess(height: int = 820) -> None:
    """Dibuja el tablero de ajedrez dentro de la app de Streamlit."""
    components.html(CHESS_HTML, height=height, scrolling=True)
