"use strict";

// The game state lives in index.html; this renderer caches exposed voxel faces
// in small chunks so camera movement does not rebuild or project the world.
function createVoxelRenderer() {
  const CHUNK_SIZE = 8;
  const CAVE_RENDER_BAND = 10;
  const NAMETAG_RANGE = 16;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1;

  const scene = new THREE.Scene();
  // The original game uses a left-handed world (+Z forward, +X right).
  const world = new THREE.Group();
  world.scale.x = -1;
  scene.add(world);
  const view = new THREE.PerspectiveCamera(70, 1, 0.1, 150);
  const ambient = new THREE.HemisphereLight(0xb9d8ff, 0x59432b, 0.6);
  const fill = new THREE.AmbientLight(0xd1deef, 0.35);
  const sun = new THREE.DirectionalLight(0xffedcd, 1.5);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -24, right: 24, top: 24, bottom: -24, near: 0.5, far: 100 });
  sun.shadow.bias = -0.001;
  sun.shadow.normalBias = 0.05;
  const moonlight = new THREE.DirectionalLight(0xb9d1ff, 0);
  moonlight.name = "moonlight";
  scene.add(ambient, fill, sun, sun.target, moonlight, moonlight.target);

  const celestialGeometry = new THREE.CircleGeometry(5, 32);
  const sunDisc = new THREE.Mesh(celestialGeometry,
    new THREE.MeshBasicMaterial({ color: 0xffe27a, toneMapped: false, depthWrite: false }));
  const moonDisc = new THREE.Mesh(celestialGeometry,
    new THREE.MeshBasicMaterial({ color: 0xdce6f5, toneMapped: false, depthWrite: false }));
  sunDisc.name = "sunDisc";
  moonDisc.name = "moonDisc";
  scene.add(sunDisc, moonDisc);
  const skyDirection = new THREE.Vector3();

  const torchLights = new Map();
  const terrainMaterial = new THREE.MeshLambertMaterial({
    vertexColors: true, side: THREE.DoubleSide, shadowSide: THREE.FrontSide
  });
  const torchMaterial = new THREE.MeshLambertMaterial({
    vertexColors: true, side: THREE.DoubleSide, shadowSide: THREE.FrontSide, emissive: 0x8b3c05
  });
  const doorMaterial = new THREE.MeshLambertMaterial({ color: ITEM_DEFINITIONS.door.color });
  const chestMaterial = new THREE.MeshLambertMaterial({ color: ITEM_DEFINITIONS.chest.color });
  const chestSeamMaterial = new THREE.MeshLambertMaterial({ color: 0x4c2b17 });
  const chestBodyGeometry = new THREE.BoxGeometry(1, 0.73, 1);
  const chestSeamGeometry = new THREE.BoxGeometry(1, 0.02, 1);
  const chestLidGeometry = new THREE.BoxGeometry(1, 0.25, 1);
  const avatarBodyGeometry = new THREE.BoxGeometry(0.65, 0.85, 0.4);
  const avatarHeadGeometry = new THREE.BoxGeometry(0.42, 0.42, 0.42);
  const avatarEyeGeometry = new THREE.BoxGeometry(0.055, 0.065, 0.01);
  const doorGeometry = new THREE.BoxGeometry(1, 1, DOOR_THICKNESS);
  const avatarHeadMaterial = new THREE.MeshLambertMaterial({ color: 0xe4bd96 });
  const avatarEyeMaterial = new THREE.MeshLambertMaterial({ color: 0x29211e });
  const arrowShaftGeometry = new THREE.BoxGeometry(0.06, 0.06, 0.7);
  const arrowTipGeometry = new THREE.ConeGeometry(0.09, 0.18, 4);
  const arrowFletchingGeometry = new THREE.BoxGeometry(0.18, 0.18, 0.12);
  const dropGeometry = new THREE.PlaneGeometry(1, 1);
  const arrowShaftMaterial = new THREE.MeshLambertMaterial({ color: 0x9b6738 });
  const arrowTipMaterial = new THREE.MeshLambertMaterial({ color: 0xc7cbd0 });
  const arrowFletchingMaterial = new THREE.MeshLambertMaterial({ color: 0xf3eee2 });
  const chunks = new Map();
  const dirty = new Set();
  const avatars = new Map();
  const arrowMeshes = new Map();
  const dropMeshes = new Map();
  const dropTextures = new Map();
  const doorSwings = new Map();
  const chestSwings = new Map();
  let band = null;

  const keyForChunk = (x, z) => `${x},${z}`;
  const chunkAt = value => Math.floor(value / CHUNK_SIZE);

  function invalidate(key) {
    const [x, , z] = key.split(",").map(Number);
    // A changed voxel can expose faces in an adjacent chunk.
    for (const [dx, dz] of [[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]]) {
      dirty.add(keyForChunk(chunkAt(x + dx), chunkAt(z + dz)));
    }
  }

  function invalidateAll() {
    for (const key of chunks.keys()) dirty.add(key);
  }

  function removeChunk(key) {
    const chunk = chunks.get(key);
    if (!chunk) return;
    for (const mesh of chunk.meshes) {
      world.remove(mesh);
      mesh.geometry.dispose();
    }
    for (const door of chunk.doors) world.remove(door.mesh);
    for (const chest of chunk.chests) world.remove(chest.group);
    chunks.delete(key);
  }

  function buildChunk(cx, cz, cameraY) {
    const arrays = {
      terrain: { positions: [], normals: [], colors: [] },
      torch: { positions: [], normals: [], colors: [] }
    };
    const doors = [];
    const chests = [];
    const torches = [];
    const startX = cx * CHUNK_SIZE;
    const startZ = cz * CHUNK_SIZE;

    function quad(target, points, normal, color) {
      const rgb = new THREE.Color(color);
      const a = points[1].map((value, i) => value - points[0][i]);
      const b = points[2].map((value, i) => value - points[0][i]);
      const front = (a[1] * b[2] - a[2] * b[1]) * normal[0] +
        (a[2] * b[0] - a[0] * b[2]) * normal[1] +
        (a[0] * b[1] - a[1] * b[0]) * normal[2] > 0;
      const indices = front ? [0, 1, 2, 0, 2, 3] : [0, 2, 1, 0, 3, 2];
      for (const i of indices) {
        target.positions.push(...points[i]);
        target.normals.push(...normal);
        target.colors.push(rgb.r, rgb.g, rgb.b);
      }
    }

    function addBlock(block) {
      const type = blockType(block);
      const { x, y, z } = block;
      if (type === "chest") {
        const group = new THREE.Group();
        group.position.set(x, y, z);
        const body = new THREE.Mesh(chestBodyGeometry, chestMaterial);
        body.position.set(0.5, 0.365, 0.5);
        const seam = new THREE.Mesh(chestSeamGeometry, chestSeamMaterial);
        seam.position.set(0.5, 0.74, 0.5);
        const hinge = new THREE.Group();
        hinge.position.set(0.5, 0.75, 1);
        const lid = new THREE.Mesh(chestLidGeometry, chestMaterial);
        lid.position.set(0, 0.125, -0.5);
        for (const mesh of [body, seam, lid]) mesh.castShadow = mesh.receiveShadow = true;
        hinge.add(lid);
        group.add(body, seam, hinge);
        world.add(group);
        chests.push({ block, group, hinge });
        return;
      }
      if (type === "door" && doorStateFromColor(block.color)) {
        const state = doorStateFromColor(block.color);
        if (!state.upper) {
          const mesh = new THREE.Mesh(doorGeometry, doorMaterial);
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          world.add(mesh);
          doors.push({ block, mesh });
        }
        return;
      }
      if (["flower_red", "flower_yellow", "flower_blue", "grass", "sapling", "crop"].includes(type)) {
        const stage = type === "crop" ? (cropStates.get(blockKey(x, y, z)) || 0) : 1;
        const height = type === "crop" ? 0.25 + stage * 0.1 : 0.72;
        const color = type === "crop" ? (stage >= 7 ? "#d6b63e" : "#6c9f32") : block.color;
        quad(arrays.terrain, [[x + 0.12, y, z + 0.12], [x + 0.88, y, z + 0.88],
          [x + 0.88, y + height, z + 0.88], [x + 0.12, y + height, z + 0.12]],
        [-Math.SQRT1_2, 0, Math.SQRT1_2], color);
        quad(arrays.terrain, [[x + 0.88, y, z + 0.12], [x + 0.12, y, z + 0.88],
          [x + 0.12, y + height, z + 0.88], [x + 0.88, y + height, z + 0.12]],
        [Math.SQRT1_2, 0, Math.SQRT1_2], color);
        return;
      }

      if (isPartialBlock(type)) {
        const color = ITEM_DEFINITIONS[type.startsWith("wood_") ? "planks" : "stone"].color;
        for (const [index, box] of blockBoxes(block).entries()) {
          const { minX, maxX, minY, maxY, minZ, maxZ } = box;
          const faces = [
            [[0, 0, -1], [[minX, minY, minZ], [maxX, minY, minZ], [maxX, maxY, minZ], [minX, maxY, minZ]]],
            [[0, 0, 1], [[maxX, minY, maxZ], [minX, minY, maxZ], [minX, maxY, maxZ], [maxX, maxY, maxZ]]],
            [[0, 1, 0], [[minX, maxY, minZ], [maxX, maxY, minZ], [maxX, maxY, maxZ], [minX, maxY, maxZ]]],
            [[-1, 0, 0], [[minX, minY, maxZ], [minX, minY, minZ], [minX, maxY, minZ], [minX, maxY, maxZ]]],
            [[1, 0, 0], [[maxX, minY, minZ], [maxX, minY, maxZ], [maxX, maxY, maxZ], [maxX, maxY, minZ]]]
          ];
          if (index === 0) faces.push(
            [[0, -1, 0], [[minX, minY, maxZ], [maxX, minY, maxZ], [maxX, minY, minZ], [minX, minY, minZ]]]
          );
          for (const [normal, points] of faces) quad(arrays.terrain, points, normal, color);
        }
        return;
      }

      const direction = type === "torch" ? torchDirection(block.color) : null;
      if (direction) {
        const [dx, dz] = direction;
        const sine = Math.sin(Math.PI / 6), cosine = Math.cos(Math.PI / 6);
        const halfWidth = 0.09;
        const offset = halfWidth * cosine;
        const baseX = x + 0.5 - dx * (0.5 - offset);
        const baseZ = z + 0.5 - dz * (0.5 - offset);
        const transform = (u, v, w, point) => {
          const along = u * cosine + v * sine;
          return [dx * along - dz * w + (point ? baseX : 0),
            -u * sine + v * cosine + (point ? y + 0.28 : 0),
            dz * along + dx * w + (point ? baseZ : 0)];
        };
        const faces = [
          [[0, 0, -1], [[-halfWidth, 0, -halfWidth], [halfWidth, 0, -halfWidth], [halfWidth, 0.72, -halfWidth], [-halfWidth, 0.72, -halfWidth]]],
          [[0, 0, 1], [[halfWidth, 0, halfWidth], [-halfWidth, 0, halfWidth], [-halfWidth, 0.72, halfWidth], [halfWidth, 0.72, halfWidth]]],
          [[0, -1, 0], [[-halfWidth, 0, halfWidth], [halfWidth, 0, halfWidth], [halfWidth, 0, -halfWidth], [-halfWidth, 0, -halfWidth]]],
          [[0, 1, 0], [[-halfWidth, 0.72, -halfWidth], [halfWidth, 0.72, -halfWidth], [halfWidth, 0.72, halfWidth], [-halfWidth, 0.72, halfWidth]]],
          [[-1, 0, 0], [[-halfWidth, 0, halfWidth], [-halfWidth, 0, -halfWidth], [-halfWidth, 0.72, -halfWidth], [-halfWidth, 0.72, halfWidth]]],
          [[1, 0, 0], [[halfWidth, 0, -halfWidth], [halfWidth, 0, halfWidth], [halfWidth, 0.72, halfWidth], [halfWidth, 0.72, -halfWidth]]]
        ];
        for (const [normal, points] of faces) {
          quad(arrays.torch, points.map(p => transform(...p, true)),
            transform(...normal, false), ITEM_DEFINITIONS.torch.color);
        }
        torches.push(transform(0, 0.72, 0, true));
        return;
      }

      const thin = type === "fence" || type === "torch";
      if (type === "torch") torches.push([x + 0.5, y + 0.7, z + 0.5]);
      const target = type === "torch" ? arrays.torch : arrays.terrain;
      const inset = type === "torch" ? 0.375 : thin ? 0.25 : 0;
      const minX = x + inset;
      const maxX = x + 1 - inset;
      const minZ = z + inset;
      const maxZ = z + 1 - inset;
      const faces = [
        [[0, 0, -1], [[minX, y, minZ], [maxX, y, minZ], [maxX, y + 1, minZ], [minX, y + 1, minZ]]],
        [[0, 0, 1], [[maxX, y, maxZ], [minX, y, maxZ], [minX, y + 1, maxZ], [maxX, y + 1, maxZ]]],
        [[0, -1, 0], [[minX, y, maxZ], [maxX, y, maxZ], [maxX, y, minZ], [minX, y, minZ]]],
        [[0, 1, 0], [[minX, y + 1, minZ], [maxX, y + 1, minZ], [maxX, y + 1, maxZ], [minX, y + 1, maxZ]]],
        [[-1, 0, 0], [[minX, y, maxZ], [minX, y, minZ], [minX, y + 1, minZ], [minX, y + 1, maxZ]]],
        [[1, 0, 0], [[maxX, y, minZ], [maxX, y, maxZ], [maxX, y + 1, maxZ], [maxX, y + 1, minZ]]]
      ];
      for (const [normal, points] of faces) {
        const [nx, ny, nz] = normal;
        if (!thin && (isOpaqueCube(x + nx, y + ny, z + nz) ||
            (type === "water" && blockType(getBlock(x + nx, y + ny, z + nz)) === "water"))) continue;
        quad(target, points, normal, block.color);
      }
    }

    for (let x = startX; x < startX + CHUNK_SIZE; x++) {
      for (let z = startZ; z < startZ + CHUNK_SIZE; z++) {
        const top = terrainHeight(x, z);
        const lowestNeighbor = Math.min(top, terrainHeight(x - 1, z), terrainHeight(x + 1, z),
          terrainHeight(x, z - 1), terrainHeight(x, z + 1));
        const surfaceLow = Math.max(WORLD_MIN_Y, lowestNeighbor - 1);
        const bandLow = Math.max(WORLD_MIN_Y, cameraY - CAVE_RENDER_BAND);
        const bandHigh = Math.min(cameraY + CAVE_RENDER_BAND + CHUNK_SIZE - 1, surfaceLow - 1);
        for (let y = bandLow; y <= bandHigh; y++) {
          const block = getBlock(x, y, z);
          if (block) addBlock(block);
        }
        for (let y = surfaceLow; y < top + 7; y++) {
          const block = getBlock(x, y, z);
          if (block) addBlock(block);
        }
      }
    }

    for (const [key, block] of placedBlocks) {
      if (!blockEdits.has(key) && chunkAt(block.x) === cx && chunkAt(block.z) === cz &&
          block.y >= terrainHeight(block.x, block.z) + 7) addBlock(block);
    }
    for (const [key, block] of blockEdits) {
      if (block && chunkAt(block.x) === cx && chunkAt(block.z) === cz &&
          block.y >= terrainHeight(block.x, block.z) + 7) addBlock(block);
    }

    const meshes = [];
    for (const [name, data] of Object.entries(arrays)) {
      if (!data.positions.length) continue;
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.Float32BufferAttribute(data.positions, 3));
      geometry.setAttribute("normal", new THREE.Float32BufferAttribute(data.normals, 3));
      geometry.setAttribute("color", new THREE.Float32BufferAttribute(data.colors, 3));
      geometry.computeBoundingSphere();
      const mesh = new THREE.Mesh(geometry, name === "torch" ? torchMaterial : terrainMaterial);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      world.add(mesh);
      meshes.push(mesh);
    }
    chunks.set(keyForChunk(cx, cz), { meshes, doors, chests, torches });
  }

  function updateDoors(dt) {
    const visible = new Set();
    for (const chunk of chunks.values()) {
      for (const { block, mesh } of chunk.doors) {
        const key = blockKey(block.x, block.y, block.z);
        visible.add(key);
        const state = doorStateFromColor(block.color);
        const target = state.open ? 1 : 0;
        let value = doorSwings.has(key) ? doorSwings.get(key) : target;
        value += Math.max(-dt / DOOR_SWING_MS, Math.min(dt / DOOR_SWING_MS, target - value));
        doorSwings.set(key, value);
        const corners = doorFootprint(state, value * Math.PI / 2);
        const height = doorPartner(block.x, block.y, block.z) ? 2 : 1;
        mesh.position.set(block.x + corners.reduce((sum, p) => sum + p[0], 0) / 4,
          block.y + height / 2, block.z + corners.reduce((sum, p) => sum + p[1], 0) / 4);
        mesh.rotation.y = -Math.atan2(corners[1][1] - corners[0][1], corners[1][0] - corners[0][0]);
        mesh.scale.y = height;
      }
    }
    for (const key of doorSwings.keys()) if (!visible.has(key)) doorSwings.delete(key);
  }

  function updateChests(dt) {
    const visible = new Set();
    for (const chunk of chunks.values()) {
      for (const { block, hinge } of chunk.chests) {
        const key = blockKey(block.x, block.y, block.z);
        visible.add(key);
        const target = chestOpen && activeChestKey === key ? 1 : 0;
        let value = chestSwings.get(key) || 0;
        value += Math.max(-dt / DOOR_SWING_MS, Math.min(dt / DOOR_SWING_MS, target - value));
        chestSwings.set(key, value);
        hinge.rotation.x = value * Math.PI / 2;
      }
    }
    for (const key of chestSwings.keys()) if (!visible.has(key)) chestSwings.delete(key);
  }

  function updateAvatars(dt) {
    for (const [id, avatar] of avatars) {
      if (!remotePlayers.has(id)) {
        world.remove(avatar.group);
        avatar.material.dispose();
        if (avatar.nametag) {
          scene.remove(avatar.nametag);
          avatar.nametag.material.map.dispose();
          avatar.nametag.material.dispose();
        }
        avatars.delete(id);
      }
    }
    for (const [id, position] of remotePlayers) {
      if (!position || !Number.isFinite(position.x) || !Number.isFinite(position.y) ||
          !Number.isFinite(position.z)) continue;
      const yaw = Number.isFinite(position.yaw) ? position.yaw : 0;
      const pitch = Number.isFinite(position.pitch)
        ? Math.max(-Math.PI / 2, Math.min(Math.PI / 2, position.pitch)) : 0;
      let avatar = avatars.get(id);
      if (!avatar) {
        const group = new THREE.Group();
        const material = new THREE.MeshLambertMaterial({ color: playerColor(id) });
        const body = new THREE.Mesh(avatarBodyGeometry, material);
        const neck = new THREE.Group();
        const head = new THREE.Mesh(avatarHeadGeometry, avatarHeadMaterial);
        body.position.y = 0.85;
        neck.position.y = 1.29;
        head.position.y = 0.21;
        for (const x of [-0.1, 0.1]) {
          const eye = new THREE.Mesh(avatarEyeGeometry, avatarEyeMaterial);
          eye.position.set(x, 0.04, 0.215);
          head.add(eye);
        }
        body.castShadow = head.castShadow = true;
        neck.add(head);
        group.add(body, neck);
        world.add(group);
        group.rotation.y = Math.atan2(Math.sin(yaw), Math.cos(yaw));
        neck.rotation.x = -pitch;
        avatar = { group, neck, material };
        avatars.set(id, avatar);
      }
      avatar.group.position.set(position.x, position.y, position.z);
      const blend = 1 - Math.exp(-Math.max(0, dt) / 100);
      const yawDelta = yaw - avatar.group.rotation.y;
      avatar.group.rotation.y += Math.atan2(Math.sin(yawDelta), Math.cos(yawDelta)) * blend;
      avatar.neck.rotation.x += (-pitch - avatar.neck.rotation.x) * blend;
      const username = remotePlayerNames.get(id);
      if (avatar.username !== username) {
        if (avatar.nametag) {
          scene.remove(avatar.nametag);
          avatar.nametag.material.map.dispose();
          avatar.nametag.material.dispose();
          avatar.nametag = null;
        }
        avatar.username = username;
        if (username) {
          const image = document.createElement("canvas");
          const context = image.getContext("2d");
          context.font = "bold 32px sans-serif";
          image.width = Math.min(1024, Math.ceil(context.measureText(username).width) + 24);
          image.height = 48;
          context.font = "bold 32px sans-serif";
          context.textAlign = "center";
          context.textBaseline = "middle";
          context.fillStyle = "rgba(0, 0, 0, 0.65)";
          context.fillRect(0, 0, image.width, image.height);
          context.fillStyle = "#ffffff";
          context.fillText(username, image.width / 2, image.height / 2, image.width - 24);
          const texture = new THREE.CanvasTexture(image);
          texture.colorSpace = THREE.SRGBColorSpace;
          avatar.nametag = new THREE.Sprite(new THREE.SpriteMaterial({
            map: texture, transparent: true, depthWrite: false, toneMapped: false
          }));
          avatar.nametag.scale.set(image.width / image.height * 0.35, 0.35, 1);
          scene.add(avatar.nametag);
        }
      }
      if (avatar.nametag) {
        avatar.nametag.position.set(-position.x, position.y + 1.95, position.z);
        avatar.nametag.visible = Math.hypot(position.x - camera.pos[0],
          position.y - camera.pos[1], position.z - camera.pos[2]) <= NAMETAG_RANGE;
      }
    }
  }

  function updateArrowMeshes() {
    const active = new Set(arrows);
    for (const [arrow, mesh] of arrowMeshes) {
      if (!active.has(arrow)) {
        scene.remove(mesh);
        arrowMeshes.delete(arrow);
      }
    }
    for (const arrow of arrows) {
      let group = arrowMeshes.get(arrow);
      if (!group) {
        group = new THREE.Group();
        const shaft = new THREE.Mesh(arrowShaftGeometry, arrowShaftMaterial);
        const tip = new THREE.Mesh(arrowTipGeometry, arrowTipMaterial);
        tip.rotation.x = Math.PI / 2;
        tip.position.z = 0.44;
        const fletching = new THREE.Mesh(arrowFletchingGeometry, arrowFletchingMaterial);
        fletching.position.z = -0.29;
        group.add(shaft, tip, fletching);
        scene.add(group);
        arrowMeshes.set(arrow, group);
      }
      const position = arrow.pickupPosition || arrow.position;
      group.position.set(-position[0], position[1], position[2]);
      group.quaternion.setFromUnitVectors(
        new THREE.Vector3(0, 0, 1),
        new THREE.Vector3(-arrow.direction[0], arrow.direction[1], arrow.direction[2]).normalize()
      );
    }
  }

  function updateDropMeshes() {
    const active = new Set(drops);
    for (const [drop, mesh] of dropMeshes) {
      if (!active.has(drop)) {
        scene.remove(mesh);
        mesh.material.dispose();
        dropMeshes.delete(drop);
      }
    }
    for (const drop of drops) {
      let mesh = dropMeshes.get(drop);
      if (!mesh) {
        let texture = dropTextures.get(drop.type);
        if (!texture) {
          const image = document.createElement("canvas");
          image.width = image.height = 128;
          const context = image.getContext("2d");
          context.font = "96px sans-serif";
          context.textAlign = "center";
          context.textBaseline = "middle";
          context.fillText(itemIcon(drop.type), 64, 68);
          texture = new THREE.CanvasTexture(image);
          texture.colorSpace = THREE.SRGBColorSpace;
          dropTextures.set(drop.type, texture);
        }
        mesh = new THREE.Mesh(dropGeometry, new THREE.MeshLambertMaterial({
          map: texture, transparent: true, side: THREE.DoubleSide
        }));
        mesh.scale.set(0.65, 0.65, 1);
        scene.add(mesh);
        dropMeshes.set(drop, mesh);
      }
      const position = drop.pickupPosition ||
        [drop.position[0], drop.fallY ?? drop.position[1], drop.position[2]];
      mesh.position.set(-position[0], position[1], position[2]);
      mesh.quaternion.copy(view.quaternion);
    }
  }

  function updateLighting() {
    const cycle = 30 * 60 * 1000;
    const phase = (Date.now() % cycle) / cycle;
    const angle = phase * Math.PI * 2 - Math.PI / 2;
    const daylight = Math.max(0, Math.sin(angle));
    const moonAmount = Math.max(0, -Math.sin(angle));
    const twilight = Math.max(0, Math.min(1, (Math.sin(angle) + 0.15) / 0.3));
    ambient.intensity = 0.4 + daylight * 0.5;
    fill.intensity = 0.4 + daylight * 0.25;
    sun.intensity = twilight * (0.35 + daylight * 1.75);
    sun.color.setHSL(0.09 + daylight * 0.04, 0.65 - daylight * 0.35, 0.68 + daylight * 0.25);
    sun.target.position.set(-camera.pos[0], camera.pos[1], camera.pos[2]);
    sun.position.set(-camera.pos[0] - Math.cos(angle) * 40,
      camera.pos[1] + Math.max(0.05, Math.sin(angle)) * 40,
      camera.pos[2] + 20);
    moonlight.intensity = moonAmount * 0.5;
    moonlight.target.position.copy(sun.target.position);
    moonlight.position.set(-camera.pos[0] + Math.cos(angle) * 40,
      camera.pos[1] + moonAmount * 40, camera.pos[2] - 20);
    skyDirection.set(-Math.cos(angle), Math.sin(angle), 0.5).normalize().multiplyScalar(100);
    sunDisc.position.copy(view.position).add(skyDirection);
    moonDisc.position.copy(view.position).sub(skyDirection);
    sunDisc.visible = Math.sin(angle) >= 0;
    moonDisc.visible = Math.sin(angle) < 0;
    sunDisc.lookAt(view.position);
    moonDisc.lookAt(view.position);
    const sky = new THREE.Color(0x263957).lerp(new THREE.Color(0xadd5f2), twilight * (0.35 + daylight * 0.65));
    scene.background = sky;
    const minutes = Math.floor(phase * 24 * 60);
    timeOfDayElement.textContent = `${String(Math.floor(minutes / 60)).padStart(2, "0")}:` +
      `${String(minutes % 60).padStart(2, "0")}` + (Math.sin(angle) < 0 ? " · Night" : " · Day");
    const activeTorches = new Set();
    for (const chunk of chunks.values()) {
      for (const position of chunk.torches) {
        const key = position.join(",");
        activeTorches.add(key);
        if (!torchLights.has(key)) {
          const light = new THREE.PointLight(0xffa044, 18, 10, 2);
          light.position.set(-position[0], position[1], position[2]);
          scene.add(light);
          torchLights.set(key, light);
        }
      }
    }
    for (const [key, light] of torchLights) {
      if (!activeTorches.has(key)) {
        scene.remove(light);
        light.dispose();
        torchLights.delete(key);
      }
    }
  }

  function render() {
    const cameraY = Math.floor(camera.pos[1] / CHUNK_SIZE) * CHUNK_SIZE;
    if (cameraY !== band) {
      band = cameraY;
      invalidateAll();
    }
    const minX = chunkAt(camera.pos[0] - RENDER_RADIUS);
    const maxX = chunkAt(camera.pos[0] + RENDER_RADIUS);
    const minZ = chunkAt(camera.pos[2] - RENDER_RADIUS);
    const maxZ = chunkAt(camera.pos[2] + RENDER_RADIUS);
    for (const key of chunks.keys()) {
      const [x, z] = key.split(",").map(Number);
      if (x < minX || x > maxX || z < minZ || z > maxZ) removeChunk(key);
    }
    const pending = [];
    for (let x = minX; x <= maxX; x++) {
      for (let z = minZ; z <= maxZ; z++) {
        const key = keyForChunk(x, z);
        if (!chunks.has(key) || dirty.has(key)) pending.push({ x, z, key,
          distance: Math.hypot((x + 0.5) * CHUNK_SIZE - camera.pos[0], (z + 0.5) * CHUNK_SIZE - camera.pos[2]) });
      }
    }
    pending.sort((a, b) => a.distance - b.distance);
    for (const chunk of pending.slice(0, 3)) {
      removeChunk(chunk.key);
      buildChunk(chunk.x, chunk.z, cameraY);
      dirty.delete(chunk.key);
    }
    // Dirty entries outside the render area need no storage: they will be
    // rebuilt from world state if the player later approaches them.
    for (const key of dirty) {
      const [x, z] = key.split(",").map(Number);
      if (x < minX || x > maxX || z < minZ || z > maxZ) dirty.delete(key);
    }
    view.position.set(-camera.pos[0], camera.pos[1] + EYE_HEIGHT, camera.pos[2]);
    const [pitch, yaw] = camera.rot;
    view.lookAt(view.position.x - Math.sin(yaw) * Math.cos(pitch),
      view.position.y + Math.sin(pitch),
      view.position.z + Math.cos(yaw) * Math.cos(pitch));
    updateDoors(frameDeltaMs);
    updateChests(frameDeltaMs);
    updateAvatars(frameDeltaMs);
    updateArrowMeshes();
    updateDropMeshes();
    updateLighting();
    renderer.render(scene, view);
  }

  function resize(width, height, ratio) {
    renderer.setPixelRatio(ratio);
    renderer.setSize(width, height, false);
    const focalLength = Math.max(1, Math.min(width, height) * 0.55);
    view.fov = 2 * Math.atan(height / (2 * focalLength)) * 180 / Math.PI;
    view.aspect = width / height;
    view.updateProjectionMatrix();
  }

  return { render, resize, invalidate, invalidateAll, scene, view, chunks, renderer, arrowMeshes, dropMeshes };
}
