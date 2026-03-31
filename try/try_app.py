import cv2
import json
import os
import math
from vision_parser import parse

IMAGE_PATH = r"..\sample\plan_a.png"
OUTPUT_DIR = "output"

WALL_HEIGHT   = 3.0
FLOOR_THICK   = 0.2
SCALE         = 0.05
GRID_UNITS    = 1800

COLORS = {
    "load_bearing_outer": "#e74c3c",
    "load_bearing_spine": "#e67e22",
    "partition":          "#95a5a6",
    "opening":            "#3498db",
    "column":             "#9b59b6",
    "bed":                "#f39c12",
    "tv_unit":            "#1abc9c",
    "floor":              "#27ae60",
}


def _m(px): return round(px * SCALE, 3)


def _norm(val, offset, scale):
    return round((val - offset) * scale, 4)


def build_threejs(data, image_w, image_h, output_path):
    geo      = data["geometry"]
    elements = geo["elements"]
    bounds   = geo["bounds"]

    layout_w = bounds["max_x"] - bounds["min_x"]
    layout_h = bounds["max_y"] - bounds["min_y"]
    if layout_w == 0 or layout_h == 0:
        layout_w, layout_h = image_w, image_h

    # Layer 4: Bounds normalization
    global_scale = GRID_UNITS / max(layout_w, layout_h)
    offset_x     = bounds["min_x"] + layout_w / 2
    offset_y     = bounds["min_y"] + layout_h / 2

    def nx(x): return round((x - offset_x) * global_scale * 0.01, 4)
    def nz(y): return round((y - offset_y) * global_scale * 0.01, 4)
    def nm(px): return round(px * global_scale * 0.01, 4)

    floor_w = round(layout_w * global_scale * 0.01, 3)
    floor_h = round(layout_h * global_scale * 0.01, 3)
    cam_dist = round(max(floor_w, floor_h) * 1.1, 2)

    # Layer 5: Build JS calls
    js_lines = []

    # Floor slab
    js_lines.append(f"addFloor(0, 0, {floor_w}, {floor_h}, {FLOOR_THICK});")

    # Edges (load-bearing outer)
    for e in elements["edges"]:
        x1, z1 = nx(e["x1"]), nz(e["y1"])
        x2, z2 = nx(e["x2"]), nz(e["y2"])
        length = round(math.hypot(x2-x1, z2-z1), 4)
        if length < 0.01: continue
        thick = 0.35
        js_lines.append(
            f"addWall({x1},{z1},{x2},{z2},{WALL_HEIGHT},{thick},{length},"
            f"'{COLORS['load_bearing_outer']}','load_bearing_outer','{e['id']}');"
        )

    # Walls
    for w in elements["walls"]:
        x1, z1 = nx(w["x1"]), nz(w["y1"])
        x2, z2 = nx(w["x2"]), nz(w["y2"])
        length = round(math.hypot(x2-x1, z2-z1), 4)
        if length < 0.01: continue
        cls   = w["wall_class"]
        thick = 0.30 if cls == "load_bearing_spine" else 0.18
        color = COLORS.get(cls, COLORS["partition"])
        js_lines.append(
            f"addWall({x1},{z1},{x2},{z2},{WALL_HEIGHT},{thick},{length},"
            f"'{color}','{cls}','{w['id']}');"
        )

    # Openings
    for op in elements["openings"]:
        x1, z1 = nx(op["x1"]), nz(op["y1"])
        x2, z2 = nx(op["x2"]), nz(op["y2"])
        length = round(math.hypot(x2-x1, z2-z1), 4)
        if length < 0.01: continue
        js_lines.append(
            f"addOpening({x1},{z1},{x2},{z2},{length},"
            f"'{COLORS['opening']}','{op['id']}');"
        )

    # Columns
    for col in elements["columns"]:
        x, z = nx(col["x"]), nz(col["y"])
        size = nm(max(col.get("w_m",1)/SCALE, col.get("h_m",1)/SCALE) * 0.5)
        size = max(0.1, min(size, 0.5))
        js_lines.append(f"addColumn({x},{z},{size},{WALL_HEIGHT},'{COLORS['column']}','{col['id']}');")

    # Furniture
    for furn in elements["furniture"]:
        x, z = nx(furn["x"]), nz(furn["y"])
        fw = nm(furn.get("w_m",2)/SCALE)
        fh = nm(furn.get("h_m",1)/SCALE)
        fw = max(0.2, min(fw, 3.0))
        fh = max(0.2, min(fh, 3.0))
        ftype = furn.get("type","bed")
        color = COLORS.get(ftype, "#f39c12")
        js_lines.append(f"addFurniture({x},{z},{fw},{fh},'{ftype}','{color}','{furn['id']}');")

    walls_js = "\n".join(js_lines)
    stats    = data["summary"]

    html = _build_html(walls_js, floor_w, floor_h, cam_dist, stats)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  3D viewer: {os.path.abspath(output_path)}")


def _build_html(scene_js, floor_w, floor_h, cam_dist, stats):
    cx = 0
    cz = 0
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Floor Plan 3D — Full Stack</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0a0a14; font-family:'Segoe UI',Arial,sans-serif; overflow:hidden; }
#info {
  position:absolute; top:14px; left:14px; z-index:10;
  background:rgba(0,0,0,0.82); color:#fff;
  padding:16px 20px; border-radius:12px;
  border:1px solid rgba(255,255,255,0.1);
  font-size:13px; min-width:200px;
}
#info h3 { color:#00d4ff; font-size:15px; margin-bottom:12px; }
.li { display:flex; align-items:center; gap:8px; margin:5px 0; font-size:12px; }
.li span { width:13px; height:13px; border-radius:3px; flex-shrink:0; }
#stats {
  position:absolute; top:14px; right:14px; z-index:10;
  background:rgba(0,0,0,0.82); color:#fff;
  padding:16px 20px; border-radius:12px;
  border:1px solid rgba(255,255,255,0.1); font-size:13px;
}
#stats h3 { color:#00d4ff; font-size:15px; margin-bottom:10px; }
#stats div { margin:4px 0; color:#94a3b8; }
#stats span { color:#fff; font-weight:600; }
#tooltip {
  position:absolute; display:none; z-index:20;
  background:rgba(0,0,0,0.9); color:#fff;
  padding:10px 14px; border-radius:8px;
  border:1px solid rgba(0,212,255,0.4);
  font-size:12px; pointer-events:none;
  max-width:220px; line-height:1.6;
}
#controls {
  position:absolute; bottom:14px; left:50%; transform:translateX(-50%);
  background:rgba(0,0,0,0.75); color:#64748b;
  padding:8px 20px; border-radius:20px; font-size:12px; z-index:10;
}
#selected-info {
  position:absolute; bottom:60px; left:50%; transform:translateX(-50%);
  background:rgba(0,212,255,0.15); color:#00d4ff;
  padding:8px 20px; border-radius:20px; font-size:13px; z-index:10;
  border:1px solid rgba(0,212,255,0.3);
  display:none; font-weight:600;
}
</style>
</head>
<body>

<div id="info">
  <h3>&#127968; Floor Plan 3D</h3>
  <div class="li"><span style="background:#e74c3c"></span>Load-bearing Outer</div>
  <div class="li"><span style="background:#e67e22"></span>Load-bearing Spine</div>
  <div class="li"><span style="background:#95a5a6"></span>Partition Wall</div>
  <div class="li"><span style="background:#3498db"></span>Opening (Door/Window)</div>
  <div class="li"><span style="background:#9b59b6"></span>Column</div>
  <div class="li"><span style="background:#f39c12"></span>Furniture (Bed)</div>
  <div class="li"><span style="background:#1abc9c"></span>Furniture (TV Unit)</div>
  <div class="li"><span style="background:#27ae60"></span>Floor Slab</div>
</div>

<div id="stats">
  <h3>Detection Stats</h3>
  <div>Outer edges: <span>""" + str(stats.get("edges",0)) + """</span></div>
  <div>Walls: <span>""" + str(stats.get("walls",0)) + """</span></div>
  <div>Openings: <span>""" + str(stats.get("openings",0)) + """</span></div>
  <div>Columns: <span>""" + str(stats.get("columns",0)) + """</span></div>
  <div>Furniture: <span>""" + str(stats.get("furniture",0)) + """</span></div>
  <div>Floor: <span>""" + str(floor_w) + """m x """ + str(floor_h) + """m</span></div>
  <div>Wall height: <span>3.0m</span></div>
</div>

<div id="tooltip"></div>
<div id="selected-info"></div>

<div id="controls">
  Left-drag: Rotate &nbsp;|&nbsp; Right-drag: Pan &nbsp;|&nbsp; Scroll: Zoom &nbsp;|&nbsp; Click: Select &nbsp;|&nbsp; Double-click: Reset
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js"></script>
<script>
// ── Scene ────────────────────────────────────────────────────
var scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a14);
scene.fog = new THREE.FogExp2(0x0a0a14, 0.018);

var W = window.innerWidth, H = window.innerHeight;
var camera = new THREE.PerspectiveCamera(45, W/H, 0.01, 500);
camera.position.set(0, """ + str(cam_dist) + """, """ + str(cam_dist*0.8) + """);
camera.lookAt(0, 0, 0);

var renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(W, H);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// ── Lights ───────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0xffffff, 0.55));
var sun = new THREE.DirectionalLight(0xffffff, 0.9);
sun.position.set(15, 30, 15);
sun.castShadow = true;
sun.shadow.mapSize.width = sun.shadow.mapSize.height = 4096;
sun.shadow.camera.left = sun.shadow.camera.bottom = -40;
sun.shadow.camera.right = sun.shadow.camera.top = 40;
scene.add(sun);
var hemi = new THREE.HemisphereLight(0x8888ff, 0x443322, 0.35);
scene.add(hemi);

// ── Grid ─────────────────────────────────────────────────────
var grid = new THREE.GridHelper(""" + str(round(max(floor_w,floor_h)*2.5,1)) + """, 40, 0x1a1a33, 0x111122);
scene.add(grid);

// ── Mesh map for click selection ─────────────────────────────
var meshMap = new Map();
var selectedMesh = null;

// ── Builders ─────────────────────────────────────────────────
function addWall(x1,z1,x2,z2,height,thick,length,color,cls,id) {
  var dx=x2-x1, dz=z2-z1;
  var angle=Math.atan2(dz,dx);
  var geo = new THREE.BoxGeometry(length, height, thick);
  var mat = new THREE.MeshPhongMaterial({
    color: new THREE.Color(color),
    shininess: 25,
    transparent: cls==='partition',
    opacity: cls==='partition' ? 0.78 : 1.0
  });
  var mesh = new THREE.Mesh(geo, mat);
  mesh.position.set((x1+x2)/2, height/2, (z1+z2)/2);
  mesh.rotation.y = -angle;
  mesh.castShadow = mesh.receiveShadow = true;
  mesh.userData = {id:id, type:cls, length_m: Math.round(length*100)/100,
                   color:color, label: cls.replace(/_/g,' ')};
  scene.add(mesh);
  meshMap.set(id+'_wall', mesh);
  var el = new THREE.EdgesGeometry(geo);
  var lm = new THREE.LineSegments(el, new THREE.LineBasicMaterial({color:0x000000,transparent:true,opacity:0.15}));
  lm.position.copy(mesh.position);
  lm.rotation.copy(mesh.rotation);
  scene.add(lm);
}

function addFloor(cx,cz,fw,fh,thick) {
  var geo = new THREE.BoxGeometry(fw, thick, fh);
  var mat = new THREE.MeshPhongMaterial({color:0x27ae60, transparent:true, opacity:0.45, shininess:5});
  var mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(cx, -thick/2, cz);
  mesh.receiveShadow = true;
  scene.add(mesh);
}

function addOpening(x1,z1,x2,z2,length,color,id) {
  var dx=x2-x1, dz=z2-z1;
  var angle=Math.atan2(dz,dx);
  var geo = new THREE.BoxGeometry(length, 2.1, 0.08);
  var mat = new THREE.MeshPhongMaterial({color:new THREE.Color(color),transparent:true,opacity:0.45,shininess:80});
  var mesh = new THREE.Mesh(geo, mat);
  mesh.position.set((x1+x2)/2, 1.05, (z1+z2)/2);
  mesh.rotation.y = -angle;
  mesh.userData = {id:id, type:'opening', label:'Opening / Door / Window'};
  scene.add(mesh);
  meshMap.set(id+'_op', mesh);
}

function addColumn(x,z,size,height,color,id) {
  var geo = new THREE.BoxGeometry(size, height, size);
  var mat = new THREE.MeshPhongMaterial({color:new THREE.Color(color), shininess:40});
  var mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(x, height/2, z);
  mesh.castShadow = true;
  mesh.userData = {id:id, type:'column', label:'Column', size_m: size};
  scene.add(mesh);
  meshMap.set(id+'_col', mesh);
}

function addFurniture(x,z,fw,fh,ftype,color,id) {
  var group = new THREE.Group();
  if (ftype === 'bed') {
    // Frame
    var frame = new THREE.Mesh(
      new THREE.BoxGeometry(fw, 0.25, fh),
      new THREE.MeshPhongMaterial({color:0x8B4513, shininess:20})
    );
    frame.position.y = 0.125;
    group.add(frame);
    // Mattress
    var matt = new THREE.Mesh(
      new THREE.BoxGeometry(fw*0.92, 0.18, fh*0.85),
      new THREE.MeshPhongMaterial({color:new THREE.Color(color), shininess:10})
    );
    matt.position.y = 0.34;
    group.add(matt);
    // Pillows
    [-fw*0.25, fw*0.25].forEach(function(px) {
      var pill = new THREE.Mesh(
        new THREE.BoxGeometry(fw*0.3, 0.1, fh*0.22),
        new THREE.MeshPhongMaterial({color:0xffffff})
      );
      pill.position.set(px, 0.47, -fh*0.3);
      group.add(pill);
    });
  } else if (ftype === 'tv_unit') {
    // Console
    var cons = new THREE.Mesh(
      new THREE.BoxGeometry(fw, 0.4, fh),
      new THREE.MeshPhongMaterial({color:0x2c3e50, shininess:60})
    );
    cons.position.y = 0.2;
    group.add(cons);
    // Screen
    var screen = new THREE.Mesh(
      new THREE.BoxGeometry(fw*0.85, fw*0.5, 0.05),
      new THREE.MeshPhongMaterial({color:0x111111, shininess:100, emissive:0x001122})
    );
    screen.position.set(0, 0.4 + fw*0.25, -fh*0.3);
    group.add(screen);
  } else {
    var box = new THREE.Mesh(
      new THREE.BoxGeometry(fw, 0.5, fh),
      new THREE.MeshPhongMaterial({color:new THREE.Color(color)})
    );
    box.position.y = 0.25;
    group.add(box);
  }
  group.position.set(x, 0, z);
  group.userData = {id:id, type:ftype, label: ftype.replace('_',' ')};
  scene.add(group);
  meshMap.set(id+'_furn', group);
}

// ── Build scene ──────────────────────────────────────────────
""" + scene_js + """

// ── Raycaster for click selection ────────────────────────────
var raycaster = new THREE.Raycaster();
var mouse     = new THREE.Vector2();
var tooltip   = document.getElementById('tooltip');
var selInfo   = document.getElementById('selected-info');

renderer.domElement.addEventListener('mousemove', function(e) {
  mouse.x =  (e.clientX / W) * 2 - 1;
  mouse.y = -(e.clientY / H) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  var meshes = [];
  meshMap.forEach(function(m) { if(m.isMesh) meshes.push(m); });
  var hits = raycaster.intersectObjects(meshes);
  if (hits.length > 0) {
    var d = hits[0].object.userData;
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX + 14) + 'px';
    tooltip.style.top  = (e.clientY - 10) + 'px';
    tooltip.innerHTML  = '<b>' + (d.label||d.type) + '</b><br>ID: ' + d.id +
      (d.length_m ? '<br>Length: ' + d.length_m + 'm' : '') +
      (d.size_m   ? '<br>Size: '   + d.size_m   + 'm' : '');
    renderer.domElement.style.cursor = 'pointer';
  } else {
    tooltip.style.display = 'none';
    renderer.domElement.style.cursor = 'default';
  }
});

renderer.domElement.addEventListener('click', function(e) {
  mouse.x =  (e.clientX / W) * 2 - 1;
  mouse.y = -(e.clientY / H) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  var meshes = [];
  meshMap.forEach(function(m) { if(m.isMesh) meshes.push(m); });
  var hits = raycaster.intersectObjects(meshes);
  if (hits.length > 0) {
    var mesh = hits[0].object;
    var d    = mesh.userData;
    if (selectedMesh && selectedMesh.material) {
      selectedMesh.material.emissive && selectedMesh.material.emissive.set(0x000000);
    }
    selectedMesh = mesh;
    if (mesh.material && mesh.material.emissive) mesh.material.emissive.set(0x00d4ff);
    selInfo.style.display = 'block';
    selInfo.textContent   = (d.label||d.type).toUpperCase() +
      (d.length_m ? '  |  ' + d.length_m + 'm' : '') + '  |  ID: ' + d.id;
    // TWEEN camera flyto
    var target = mesh.position.clone();
    var from   = {x:camera.position.x, y:camera.position.y, z:camera.position.z};
    var to     = {x:target.x, y:target.y+4, z:target.z+6};
    new TWEEN.Tween(from).to(to, 800)
      .easing(TWEEN.Easing.Quadratic.InOut)
      .onUpdate(function() { camera.position.set(from.x, from.y, from.z); camera.lookAt(target); })
      .start();
  }
});

// ── Orbit controls ───────────────────────────────────────────
var isDrag=false, isRight=false, px=0, py=0;
var theta=0.5, phi=0.85, radius=""" + str(cam_dist) + """;
var tx=0, tz=0;

function updateCam() {
  camera.position.x = tx + radius*Math.sin(phi)*Math.sin(theta);
  camera.position.y = radius*Math.cos(phi);
  camera.position.z = tz + radius*Math.sin(phi)*Math.cos(theta);
  camera.lookAt(tx, 0, tz);
}
updateCam();

renderer.domElement.addEventListener('mousedown', function(e){
  isDrag=true; isRight=(e.button===2); px=e.clientX; py=e.clientY;
});
renderer.domElement.addEventListener('contextmenu', function(e){ e.preventDefault(); });
window.addEventListener('mouseup', function(){ isDrag=false; });
window.addEventListener('mousemove', function(e){
  if(!isDrag) return;
  var dx=e.clientX-px, dy=e.clientY-py;
  if(isRight){ tx-=dx*0.03; tz-=dy*0.03; }
  else { theta-=dx*0.005; phi=Math.max(0.05,Math.min(1.55,phi+dy*0.005)); }
  px=e.clientX; py=e.clientY;
  updateCam();
});
renderer.domElement.addEventListener('wheel', function(e){
  radius=Math.max(1,Math.min(200,radius+e.deltaY*0.05));
  updateCam();
});
renderer.domElement.addEventListener('dblclick', function(){
  theta=0.5; phi=0.85; radius=""" + str(cam_dist) + """;
  tx=0; tz=0; updateCam();
  if(selectedMesh && selectedMesh.material && selectedMesh.material.emissive)
    selectedMesh.material.emissive.set(0x000000);
  selectedMesh=null;
  selInfo.style.display='none';
});
window.addEventListener('resize', function(){
  W=window.innerWidth; H=window.innerHeight;
  camera.aspect=W/H; camera.updateProjectionMatrix();
  renderer.setSize(W,H);
});

function animate() {
  requestAnimationFrame(animate);
  TWEEN.update();
  renderer.render(scene, camera);
}
animate();
</script>
</body>
</html>"""


if __name__ == "__main__":
    print(f"\n{'='*55}")
    print("  TRY — Full 2D → 3D Stack")
    print(f"{'='*55}\n")

    if not os.path.exists(IMAGE_PATH):
        print(f"  ERROR: {IMAGE_PATH} not found")
        exit(1)

    img = cv2.imread(IMAGE_PATH)
    H, W = img.shape[:2]

    print("[1/2] Running vision parser...")
    data = parse(IMAGE_PATH)

    with open(os.path.join(OUTPUT_DIR, "geometry.json") if os.path.exists(OUTPUT_DIR) else "geometry.json", "w") as f:
        geo_out = {k: v for k, v in data.items() if k != "geometry"}
        geo_out["summary"] = data["summary"]
        json.dump(geo_out, f, indent=2)

    print("\n[2/2] Building Three.js 3D model...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "model_3d.html")
    build_threejs(data, W, H, out_path)

    print(f"\n{'='*55}")
    print("  DONE")
    print(f"{'='*55}")
    print(f"  Open in Chrome: {os.path.abspath(out_path)}")
    print(f"{'='*55}\n")
