import os

WALL_HEIGHT  = 3.0
FLOOR_HEIGHT = 0.2
SCALE        = 0.05   # 1px = 0.05m  so 937px = ~47m fits well in 3D

COLORS = {
    "load_bearing_outer": "#c0392b",
    "load_bearing_spine": "#e67e22",
    "partition":          "#bdc3c7"
}


def _m(px):
    return round(px * SCALE, 3)


def export_threejs(classified_edges, rooms, image_w, image_h, output_path):
    w  = _m(image_w)
    h  = _m(image_h)
    cx = round(w / 2, 3)
    cz = round(h / 2, 3)
    cam_y = round(max(w, h) * 0.9, 2)
    cam_z = round(max(w, h) * 0.7, 2)

    # wall thickness based on classification
    walls_js = _walls_js(classified_edges, image_h)
    floor_js = "addFloor(" + str(cx) + "," + str(cz) + "," + str(w) + "," + str(h) + "," + str(FLOOR_HEIGHT) + ");"
    rooms_js = _rooms_js(rooms, image_h)
    dist_js  = _distance_labels(classified_edges, image_h)

    stats = _stats(classified_edges, rooms, w, h)

    html = _build_html(walls_js, floor_js, rooms_js, dist_js, stats, w, h, cx, cz, cam_y, cam_z)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("  3D viewer : " + os.path.abspath(output_path))


def _walls_js(edges, image_h):
    lines = []
    for e in edges:
        x1     = _m(e["x1"])
        z1     = _m(image_h - e["y1"])
        x2     = _m(e["x2"])
        z2     = _m(image_h - e["y2"])
        length = _m(e["length"])
        color  = COLORS.get(e["wall_class"], "#bdc3c7")
        cls    = e["wall_class"]
        thick  = 0.6 if "load_bearing" in cls else 0.3
        lines.append(
            "addWall(" + str(x1) + "," + str(z1) + "," +
            str(x2) + "," + str(z2) + "," +
            str(WALL_HEIGHT) + "," + str(thick) + "," +
            str(length) + ",'" + color + "','" + cls + "');"
        )
    return "\n".join(lines)


def _rooms_js(rooms, image_h):
    lines = []
    for r in rooms:
        b  = r["bbox"]
        cx = _m(b["x"] + b["w"] / 2)
        cz = _m(image_h - (b["y"] + b["h"] / 2))
        rw = round(_m(b["w"]), 2)
        rh = round(_m(b["h"]), 2)
        lines.append("addRoomMarker(" + str(cx) + "," + str(cz) + "," + str(rw) + "," + str(rh) + ");")
    return "\n".join(lines)


def _distance_labels(edges, image_h):
    lines = []
    # Only label load-bearing walls with their length
    for e in edges:
        if e["wall_class"] == "partition":
            continue
        mx = _m((e["x1"] + e["x2"]) / 2)
        mz = _m(image_h - (e["y1"] + e["y2"]) / 2)
        dist = round(_m(e["length"]), 1)
        lines.append("addDistLabel(" + str(mx) + "," + str(mz) + ",'" + str(dist) + "m');")
    return "\n".join(lines)


def _stats(edges, rooms, w, h):
    outer = len([e for e in edges if e["wall_class"] == "load_bearing_outer"])
    spine = len([e for e in edges if e["wall_class"] == "load_bearing_spine"])
    parts = len([e for e in edges if e["wall_class"] == "partition"])
    return {
        "floor_w": w, "floor_h": h,
        "outer": outer, "spine": spine, "partition": parts,
        "rooms": len(rooms), "total_walls": len(edges)
    }


def _build_html(walls_js, floor_js, rooms_js, dist_js, stats, w, h, cx, cz, cam_y, cam_z):
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Floor Plan 3D Viewer</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0f0f1a; font-family:Arial,sans-serif; overflow:hidden; }
#info {
  position:absolute; top:14px; left:14px;
  background:rgba(0,0,0,0.8); color:#fff;
  padding:14px 18px; border-radius:10px; font-size:13px; z-index:10;
  border:1px solid rgba(255,255,255,0.1);
}
#info h3 { margin-bottom:10px; color:#00d4ff; font-size:15px; }
.li { display:flex; align-items:center; gap:8px; margin:5px 0; }
.li span { width:14px; height:14px; border-radius:3px; flex-shrink:0; }
#stats {
  position:absolute; top:14px; right:14px;
  background:rgba(0,0,0,0.8); color:#fff;
  padding:14px 18px; border-radius:10px; font-size:13px; z-index:10;
  border:1px solid rgba(255,255,255,0.1);
}
#stats h3 { color:#00d4ff; margin-bottom:8px; font-size:15px; }
#stats div { margin:3px 0; color:#ccc; }
#stats span { color:#fff; font-weight:bold; }
#controls {
  position:absolute; bottom:14px; left:50%; transform:translateX(-50%);
  background:rgba(0,0,0,0.75); color:#888;
  padding:8px 20px; border-radius:20px; font-size:12px; z-index:10;
  border:1px solid rgba(255,255,255,0.08);
}
#toggle {
  position:absolute; bottom:14px; right:14px;
  background:rgba(0,0,0,0.8); color:#fff;
  padding:8px 14px; border-radius:8px; font-size:12px; z-index:10;
  border:1px solid rgba(255,255,255,0.15); cursor:pointer;
}
#toggle:hover { background:rgba(0,100,200,0.6); }
</style>
</head>
<body>

<div id="info">
  <h3>&#127968; Floor Plan 3D</h3>
  <div class="li"><span style="background:#c0392b"></span>Load-bearing Outer</div>
  <div class="li"><span style="background:#e67e22"></span>Load-bearing Spine</div>
  <div class="li"><span style="background:#bdc3c7"></span>Partition Wall</div>
  <div class="li"><span style="background:#2ecc71"></span>Floor Slab</div>
  <div class="li"><span style="background:#00d4ff"></span>Room Center</div>
</div>

<div id="stats">
  <h3>Model Info</h3>
  <div>Floor size: <span>""" + str(w) + """m x """ + str(h) + """m</span></div>
  <div>Wall height: <span>3.0m</span></div>
  <div>Total walls: <span>""" + str(stats["total_walls"]) + """</span></div>
  <div>Load-bearing outer: <span>""" + str(stats["outer"]) + """</span></div>
  <div>Load-bearing spine: <span>""" + str(stats["spine"]) + """</span></div>
  <div>Partition: <span>""" + str(stats["partition"]) + """</span></div>
  <div>Rooms: <span>""" + str(stats["rooms"]) + """</span></div>
</div>

<div id="controls">
  Left-drag: Rotate &nbsp;|&nbsp; Right-drag: Pan &nbsp;|&nbsp; Scroll: Zoom &nbsp;|&nbsp; Double-click: Reset view
</div>

<button id="toggle" onclick="toggleLabels()">Toggle Distance Labels</button>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
var scene = new THREE.Scene();
scene.background = new THREE.Color(0x0f0f1a);
scene.fog = new THREE.FogExp2(0x0f0f1a, 0.012);

var W = window.innerWidth, H = window.innerHeight;
var camera = new THREE.PerspectiveCamera(45, W/H, 0.1, 1000);
camera.position.set(""" + str(cx) + """, """ + str(cam_y) + """, """ + str(cam_z) + """);
camera.lookAt(""" + str(cx) + """, 0, """ + str(cz) + """);

var renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
renderer.setSize(W, H);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// Lights
scene.add(new THREE.AmbientLight(0xffffff, 0.5));
var sun = new THREE.DirectionalLight(0xffffff, 1.0);
sun.position.set(""" + str(cx) + """ + 20, 40, """ + str(cz) + """ + 20);
sun.castShadow = true;
sun.shadow.mapSize.width = 4096;
sun.shadow.mapSize.height = 4096;
sun.shadow.camera.near = 0.5;
sun.shadow.camera.far = 200;
sun.shadow.camera.left = -60;
sun.shadow.camera.right = 60;
sun.shadow.camera.top = 60;
sun.shadow.camera.bottom = -60;
scene.add(sun);
var fill = new THREE.DirectionalLight(0x4488ff, 0.4);
fill.position.set(-20, 20, -20);
scene.add(fill);
var back = new THREE.DirectionalLight(0xffaa44, 0.2);
back.position.set(0, -10, -30);
scene.add(back);

// Grid
var grid = new THREE.GridHelper(""" + str(round(max(w,h)*2,1)) + """, 50, 0x222244, 0x1a1a33);
grid.position.set(""" + str(cx) + """, -0.01, """ + str(cz) + """);
scene.add(grid);

// Labels group (toggleable)
var labelsGroup = new THREE.Group();
scene.add(labelsGroup);

function toggleLabels() {
  labelsGroup.visible = !labelsGroup.visible;
}

// Wall
function addWall(x1,z1,x2,z2,height,thick,length,color,cls) {
  var dx=x2-x1, dz=z2-z1;
  var wcx=(x1+x2)/2, wcz=(z1+z2)/2;
  var angle=Math.atan2(dz,dx);
  var geo = new THREE.BoxGeometry(length, height, thick);
  var mat = new THREE.MeshPhongMaterial({
    color: new THREE.Color(color),
    shininess: 30,
    transparent: cls==='partition',
    opacity: cls==='partition' ? 0.75 : 1.0
  });
  var mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(wcx, height/2, wcz);
  mesh.rotation.y = -angle;
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  // Edge lines
  var el = new THREE.EdgesGeometry(geo);
  var lm = new THREE.LineSegments(el, new THREE.LineBasicMaterial({color:0x000000, transparent:true, opacity:0.2}));
  lm.position.copy(mesh.position);
  lm.rotation.copy(mesh.rotation);
  scene.add(lm);
}

// Floor
function addFloor(cx,cz,fw,fh,thick) {
  var geo = new THREE.BoxGeometry(fw, thick, fh);
  var mat = new THREE.MeshPhongMaterial({color:0x27ae60, transparent:true, opacity:0.5, shininess:10});
  var mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(cx, -thick/2, cz);
  mesh.receiveShadow = true;
  scene.add(mesh);
}

// Room marker
function addRoomMarker(cx,cz,rw,rh) {
  var geo = new THREE.CylinderGeometry(0.15,0.15,0.05,16);
  var mat = new THREE.MeshBasicMaterial({color:0x00d4ff});
  var m = new THREE.Mesh(geo,mat);
  m.position.set(cx,0.03,cz);
  scene.add(m);
  // Room floor highlight
  var fgeo = new THREE.PlaneGeometry(rw*0.85, rh*0.85);
  var fmat = new THREE.MeshBasicMaterial({color:0x00d4ff, transparent:true, opacity:0.06, side:THREE.DoubleSide});
  var fmesh = new THREE.Mesh(fgeo, fmat);
  fmesh.rotation.x = -Math.PI/2;
  fmesh.position.set(cx, 0.02, cz);
  scene.add(fmesh);
}

// Distance label (sprite)
function addDistLabel(mx,mz,text) {
  var canvas = document.createElement('canvas');
  canvas.width = 128; canvas.height = 40;
  var ctx = canvas.getContext('2d');
  ctx.fillStyle = 'rgba(0,0,0,0.7)';
  ctx.roundRect(2,2,124,36,6);
  ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 18px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 64, 20);
  var tex = new THREE.CanvasTexture(canvas);
  var mat = new THREE.SpriteMaterial({map:tex, transparent:true});
  var sprite = new THREE.Sprite(mat);
  sprite.scale.set(2.5, 0.8, 1);
  sprite.position.set(mx, """ + str(WALL_HEIGHT) + """ + 0.5, mz);
  labelsGroup.add(sprite);
}

// Build scene
""" + floor_js + """
""" + walls_js + """
""" + rooms_js + """
""" + dist_js + """

// Orbit controls
var isDrag=false, isRight=false, px=0, py=0;
var theta=0.6, phi=0.75, radius=""" + str(cam_y) + """;
var tx=""" + str(cx) + """, tz=""" + str(cz) + """;

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
  radius=Math.max(3,Math.min(150,radius+e.deltaY*0.05));
  updateCam();
});
renderer.domElement.addEventListener('dblclick', function(){
  theta=0.6; phi=0.75; radius=""" + str(cam_y) + """;
  tx=""" + str(cx) + """; tz=""" + str(cz) + """;
  updateCam();
});
window.addEventListener('resize', function(){
  camera.aspect=window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth,window.innerHeight);
});

function animate(){ requestAnimationFrame(animate); renderer.render(scene,camera); }
animate();
</script>
</body>
</html>"""
