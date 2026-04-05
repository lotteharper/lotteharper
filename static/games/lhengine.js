const canvas = document.getElementById('lhengine-canvas');
const ctx = canvas.getContext('2d');
const w = 600, h = 400;
canvas.width = w; canvas.height = h;
const cx = w / 2, cy = h / 2;

const GRAVITY = 20.0;
const JUMP_FORCE = -8.0;
const GROUND_LEVEL = -2;
const PLAYER_RADIUS = 0.3; // Distance from center for wall collisions

function rotate2d(x, y, rad) {
    const s = Math.sin(rad), c = Math.cos(rad);
    return [x * c - y * s, y * c + x * s];
}

// --- Camera Class with Physics & Collision ---
class Cam {
    constructor() {
        this.pos = [0, 1.7, -8];
        this.rot = [0, 0];
        this.velY = 0;
        this.isGrounded = false;
    }

    update(dt, keys, colliders) {
        const speed = dt * 8;
        let nextX = this.pos[0];
        let nextZ = this.pos[2];
        
        // 1. Calculate Movement Intent
        const xDir = Math.sin(this.rot[1]);
        const zDir = Math.cos(this.rot[1]);

        if (keys['w']) { nextX += xDir * speed; nextZ += zDir * speed; }
        if (keys['s']) { nextX -= xDir * speed; nextZ -= zDir * speed; }
        if (keys['a']) { nextX -= zDir * speed; nextZ += xDir * speed; }
        if (keys['d']) { nextX += zDir * speed; nextZ -= xDir * speed; }

        // 2. Collision Detection (AABB)
        // Check X movement
        if (!this.checkCollision(nextX, this.pos[1], this.pos[2], colliders)) {
            this.pos[0] = nextX;
        }
        // Check Z movement
        if (!this.checkCollision(this.pos[0], this.pos[1], nextZ, colliders)) {
            this.pos[2] = nextZ;
        }

        // 3. Gravity & Jumping
        if (keys[' '] && this.isGrounded) {
            this.velY = JUMP_FORCE;
            this.isGrounded = false;
        }

        this.velY += GRAVITY * dt;
        let nextY = this.pos[1] + this.velY * dt;

        // Ground/Ceiling Collision
        if (nextY > GROUND_LEVEL + 1.6) {
            nextY = GROUND_LEVEL + 1.6;
            this.velY = 0;
            this.isGrounded = true;
        } else {
            // Check if we hit a cube vertically
            if(this.checkCollision(this.pos[0], nextY, this.pos[2], colliders)) {
                this.velY = 0;
                nextY = this.pos[1]; 
            }
        }
        this.pos[1] = nextY;
    }

    checkCollision(x, y, z, objects) {
        for (let obj of objects) {
            if (obj instanceof Ground) continue; // Ground handled by GROUND_LEVEL
            
            // Basic AABB check: Is the player point + radius inside the cube?
            const b = obj.bounds;
            if (x + PLAYER_RADIUS > b.minX && x - PLAYER_RADIUS < b.maxX &&
                y + PLAYER_RADIUS > b.minY && y - PLAYER_RADIUS < b.maxY &&
                z + PLAYER_RADIUS > b.minZ && z - PLAYER_RADIUS < b.maxZ) {
                return true;
            }
        }
        return false;
    }
}

class Cube {
    constructor(pos, size = 1, color = '#888') {
        const [x, y, z] = pos;
        const s = size / 2;
        this.color = color;
        this.verts = [
            [x-s,y-s,z-s], [x+s,y-s,z-s], [x+s,y+s,z-s], [x-s,y+s,z-s],
            [x-s,y-s,z+s], [x+s,y-s,z+s], [x+s,y+s,z+s], [x-s,y+s,z+s]
        ];
        this.faces = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[0,3,7,4],[1,2,6,5]];
        // Pre-calculate bounding box for collision
        this.bounds = {
            minX: x - s, maxX: x + s,
            minY: y - s, maxY: y + s,
            minZ: z - s, maxZ: z + s
        };
    }
}

class Ground {
    constructor() {
        const size = 20, y = 1.5;
        this.color = '#3ea33e';
        this.verts = [[-size, y, -size], [size, y, -size], [size, y, size], [-size, y, size]];
        this.faces = [[0, 1, 2, 3]];
    }
}

const cam = new Cam();
class Perlin {
    constructor() {
        this.p = new Uint8Array(512);
        const perm = Array.from({length: 256}, (_, i) => i);
        // Shuffle...
        for (let i = 255; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [perm[i], perm[j]] = [perm[j], perm[i]];
        }
        for (let i = 0; i < 512; i++) this.p[i] = perm[i & 255];
    }
    fade(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
    lerp(t, a, b) { return a + t * (b - a); }
    grad(hash, x, y, z) {
        const h = hash & 15;
        const u = h < 8 ? x : y, v = h < 4 ? y : h === 12 || h === 14 ? x : z;
        return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
    }
    noise(x, y, z = 0) {
        const X = Math.floor(x) & 255, Y = Math.floor(y) & 255, Z = Math.floor(z) & 255;
        x -= Math.floor(x); y -= Math.floor(y); z -= Math.floor(z);
        const u = this.fade(x), v = this.fade(y), w = this.fade(z);
        const A = this.p[X] + Y, AA = this.p[A] + Z, AB = this.p[A + 1] + Z;
        const B = this.p[X + 1] + Y, BA = this.p[B] + Z, BB = this.p[B + 1] + Z;
        return this.lerp(w, 
            this.lerp(v, this.lerp(u, this.grad(this.p[AA], x, y, z), this.grad(this.p[BA], x-1, y, z)),
                         this.lerp(u, this.grad(this.p[AB], x, y-1, z), this.grad(this.p[BB], x-1, y-1, z))),
            this.lerp(v, this.lerp(u, this.grad(this.p[AA+1], x, y, z-1), this.grad(this.p[BA+1], x-1, y, z-1)),
                         this.lerp(u, this.grad(this.p[AB+1], x, y-1, z-1), this.grad(this.p[BB+1], x-1, y-1, z-1)))
        );
    }
}
var worldObjects = [
/*    new Ground(),*/
    new Cube([0, 0, 0], 1, '#ff4444'),
    new Cube([-4, 0, 3], 1, '#4444ff'),
/*    new Cube([4, 0, 3], 1, '#ffff44'),
    new Cube([0, 0, 3], 1, '#44ff44')*/
];
var perlin = new Perlin();
for(var x = 0; x < 32; x++) {
    for(var z = 0; z < 32; z++) {
       for(var y = 0; y < 8; y++) {

size = 1024;
vertextHeight = perlin((vertexX + offsetX) / size, (vertextY + offsetY) / size)`
            var height = Math.floor(perlin.noise(x+0.5,0.5,z+0.5)*3 + y);
           if(x == 0 || x == 31 || z == 0 || z == 31 || y == 0 || y == height) {
               worldObjects.push(new Cube([x,height,z], 1, '#ff4444'));
           }
       }
    }
}
const keys = {};
let lastTime = 0;

window.onkeydown = (e) => keys[e.key.toLowerCase()] = true;
window.onkeyup = (e) => keys[e.key.toLowerCase()] = false;
canvas.onclick = () => canvas.requestPointerLock();
document.onmousemove = (e) => {
    if (document.pointerLockElement === canvas) {
        cam.rot[1] += e.movementX / 500;
        cam.rot[0] = Math.max(-1.5, Math.min(1.5, cam.rot[0] + e.movementY / 500));
    }
};

function loop(time) {
    const dt = Math.min((time - lastTime) / 1000, 0.1);
    lastTime = time;

    cam.update(dt || 0, keys, worldObjects);

    ctx.fillStyle = '#87CEEB';
    ctx.fillRect(0, 0, w, h);

    let allFaces = [];
    worldObjects.forEach(obj => {
        let vertList = [];
        let screenCoords = [];

        obj.verts.forEach(v => {
            let [x, y, z] = v;
            x -= cam.pos[0]; y -= cam.pos[1]; z -= cam.pos[2];
            [x, z] = rotate2d(x, z, cam.rot[1]);
            [y, z] = rotate2d(y, z, cam.rot[0]);
            vertList.push([x, y, z]);
            const f = 400 / Math.max(z, 0.01);
            screenCoords.push([cx + (x * f), cy + (y * f)]);
        });

        obj.faces.forEach(faceIndices => {
            const faceVerts = faceIndices.map(i => vertList[i]);
            if (faceVerts.some(v => v[2] > 0.1)) {
                const avgZ = faceVerts.reduce((sum, v) => sum + v[2], 0) / faceIndices.length;
                allFaces.push({
                    coords: faceIndices.map(i => screenCoords[i]),
                    depth: avgZ,
                    color: obj.color
                });
            }
        });
    });

    allFaces.sort((a, b) => b.depth - a.depth);
    allFaces.forEach(f => {
        ctx.beginPath();
        ctx.moveTo(f.coords[0][0], f.coords[0][1]);
        for (let i = 1; i < f.coords.length; i++) ctx.lineTo(f.coords[i][0], f.coords[i][1]);
        ctx.closePath();
        ctx.fillStyle = f.color;
        ctx.fill();
        ctx.strokeStyle = 'rgba(0,0,0,0.3)';
        ctx.stroke();
    });

    requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
