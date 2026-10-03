"use strict";

// =============================================================================
// DOM REFERENCES
// =============================================================================

const canvas = document.getElementById("c");
const context = canvas.getContext("2d");

const hotbarElement = document.getElementById("hotbar");
const inventoryPanel = document.getElementById("inventoryPanel");
const inventoryGrid = document.getElementById("inventoryGrid");
const craftingRecipesElement =
  document.getElementById("craftingRecipes");
const craftStatusElement = document.getElementById("craftStatus");
const controllerStatus = document.getElementById("controllerStatus");
const mineProgressElement = document.getElementById("mineProgress");
const coordinatesElement = document.getElementById("coordinates");
const statusElement = document.getElementById("gameStatus");
const containerPanel = document.getElementById("containerPanel");
const containerTitleElement =
  document.getElementById("containerTitle");
const containerGrid = document.getElementById("containerGrid");
const containerInfoElement =
  document.getElementById("containerInfo");
const containerCloseButton =
  document.getElementById("containerClose");

// =============================================================================
// CONSTANTS
// =============================================================================

const WORLD_MIN_Y = -24;
const WORLD_SEED = 123456;
const RENDER_RADIUS = 16;

const PLAYER_HALF_WIDTH = 0.28;
const PLAYER_HEIGHT = 1.7;
const EYE_HEIGHT = 1.6;

const MOVE_SPEED = 5;
const GRAVITY = 18;
const JUMP_SPEED = 7;
const MAX_STEP_HEIGHT = 1;

const MINE_DURATION_MS = 1000;
const PLACE_COOLDOWN_MS = 250;

// =============================================================================
// CANVAS
// =============================================================================

let screenWidth = 0;
let screenHeight = 0;
let centerX = 0;
let centerY = 0;

function resizeCanvas() {
  const devicePixelRatio = Math.min(window.devicePixelRatio || 1, 2);

  screenWidth = window.innerWidth;
  screenHeight = window.innerHeight;

  canvas.width = Math.round(screenWidth * devicePixelRatio);
  canvas.height = Math.round(screenHeight * devicePixelRatio);

  context.setTransform(
    devicePixelRatio,
    0,
    0,
    devicePixelRatio,
    0,
    0,
  );

  centerX = screenWidth / 2;
  centerY = screenHeight / 2;
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();

// =============================================================================
// TERRAIN GENERATION
// =============================================================================

function createPermutation(seed) {
  const values = Array.from({ length: 256 }, (_, index) => index);
  let state = seed >>> 0;

  for (let index = values.length - 1; index > 0; index -= 1) {
    state = (1664525 * state + 1013904223) >>> 0;

    const randomIndex = Math.floor(
      (state / 4294967296) * (index + 1),
    );

    [values[index], values[randomIndex]] = [
      values[randomIndex],
      values[index],
    ];
  }

  return [...values, ...values];
}

function fade(value) {
  return value * value * value * (value * (value * 6 - 15) + 10);
}

function lerp(start, end, amount) {
  return start + (end - start) * amount;
}

function gradient(hash, x, y) {
  switch (hash & 7) {
    case 0:
      return x + y;
    case 1:
      return -x + y;
    case 2:
      return x - y;
    case 3:
      return -x - y;
    case 4:
      return x;
    case 5:
      return -x;
    case 6:
      return y;
    default:
      return -y;
  }
}

const permutation = createPermutation(WORLD_SEED);

function perlin2(x, y) {
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);

  const xIndex = x0 & 255;
  const yIndex = y0 & 255;

  const localX = x - x0;
  const localY = y - y0;

  const fadeX = fade(localX);
  const fadeY = fade(localY);

  const topLeft = permutation[permutation[xIndex] + yIndex];
  const topRight = permutation[permutation[xIndex] + yIndex + 1];
  const bottomLeft = permutation[permutation[xIndex + 1] + yIndex];
  const bottomRight =
    permutation[permutation[xIndex + 1] + yIndex + 1];

  const top = lerp(
    gradient(topLeft, localX, localY),
    gradient(topRight, localX, localY - 1),
    fadeY,
  );

  const bottom = lerp(
    gradient(bottomLeft, localX - 1, localY),
    gradient(bottomRight, localX - 1, localY - 1),
    fadeY,
  );

  return 0.7 * lerp(top, bottom, fadeX);
}

function smoothstep(start, end, value) {
  const normalized = Math.max(
    0,
    Math.min(1, (value - start) / (end - start)),
  );

  return normalized * normalized * (3 - 2 * normalized);
}

function computeTerrainHeight(x, z) {
  let value = 0;
  let amplitude = 1;
  let frequency = 1;
  let amplitudeTotal = 0;

  for (let octave = 0; octave < 5; octave += 1) {
    value += perlin2(
      (x * frequency) / 26,
      (z * frequency) / 26,
    ) * amplitude;

    amplitudeTotal += amplitude;
    amplitude *= 0.52;
    frequency *= 2;
  }

  const baseHeight = 2 + (value / amplitudeTotal) * 18;
  const broadNoise = smoothstep(
    0.14,
    0.44,
    perlin2(x / 165, z / 165),
  );

  const detailNoise = perlin2(x / 34, z / 34);
  const detailFactor = Math.max(
    0,
    1 - Math.abs(detailNoise) / 0.7,
  );

  const largeNoise = perlin2(x / 76, z / 76);
  const largeFactor = Math.max(
    0,
    Math.min(1, (largeNoise + 0.7) / 1.4),
  );

  return Math.floor(
    baseHeight +
      broadNoise * (2 + 12 * detailFactor + 5 * largeFactor),
  );
}

const terrainHeightCache = new Map();

function terrainHeight(x, z) {
  const key = `${x},${z}`;
  let height = terrainHeightCache.get(key);

  if (height === undefined) {
    if (terrainHeightCache.size > 200000) {
      terrainHeightCache.clear();
    }

    height = computeTerrainHeight(x, z);
    terrainHeightCache.set(key, height);
  }

  return height;
}

function terrainColor(y) {
  if (y < -4) return "#655244";
  if (y < 0) return "#826344";
  if (y < 4) return "#718b45";
  if (y < 9) return "#82934b";
  return "#a5a16e";
}

// =============================================================================
// ITEMS, BLOCKS, AND DOORS
// =============================================================================

const MAX_STACK = 64;

// The server only stores block colors, so every item/block color must be
// unique: block types are recovered from colors on reload.

// Mining tiers: the number is the tier of the tool, 0 being bare hands.
const TOOL_TIER_PREFIXES = [
  "",
  "wood",
  "stone",
  "copper",
  "iron",
];

const ITEM_DEFINITIONS = {
  log: {
    name: "Wood",
    color: "#76502e",
  },
  planks: {
    name: "Planks",
    color: "#b9824a",
  },
  sticks: {
    name: "Sticks",
    color: "#c99355",
  },
  stone: {
    name: "Stone",
    color: "#777b82",
  },
  dirt: {
    name: "Dirt",
    color: "#826344",
  },
  leaves: {
    name: "Leaves",
    color: "#32853b",
  },
  coal: {
    name: "Coal",
    color: "#25262a",
    placeable: false,
  },
  raw_copper: {
    name: "Raw Copper",
    color: "#d98b5b",
    placeable: false,
  },
  raw_iron: {
    name: "Raw Iron",
    color: "#d3b8a4",
    placeable: false,
  },
  raw_gold: {
    name: "Raw Gold",
    color: "#f0d24c",
    placeable: false,
  },
  copper_ingot: {
    name: "Copper Ingot",
    color: "#e0773d",
    placeable: false,
  },
  iron_ingot: {
    name: "Iron Ingot",
    color: "#d8dde3",
    placeable: false,
  },
  gold_ingot: {
    name: "Gold Ingot",
    color: "#ffd83a",
    placeable: false,
  },
  wood_pickaxe: {
    name: "Wood Pickaxe",
    color: "#d9ad55",
    tool: { kind: "pickaxe", tier: 1 },
    placeable: false,
  },
  stone_pickaxe: {
    name: "Stone Pickaxe",
    color: "#98a4b5",
    tool: { kind: "pickaxe", tier: 2 },
    placeable: false,
  },
  copper_pickaxe: {
    name: "Copper Pickaxe",
    color: "#c4673a",
    tool: { kind: "pickaxe", tier: 3 },
    placeable: false,
  },
  iron_pickaxe: {
    name: "Iron Pickaxe",
    color: "#c5ccd3",
    tool: { kind: "pickaxe", tier: 4 },
    placeable: false,
  },
  wood_axe: {
    name: "Wood Axe",
    color: "#bf8d43",
    tool: { kind: "axe", tier: 1 },
    placeable: false,
  },
  stone_axe: {
    name: "Stone Axe",
    color: "#687b91",
    tool: { kind: "axe", tier: 2 },
    placeable: false,
  },
  copper_axe: {
    name: "Copper Axe",
    color: "#b35a31",
    tool: { kind: "axe", tier: 3 },
    placeable: false,
  },
  iron_axe: {
    name: "Iron Axe",
    color: "#aeb7c0",
    tool: { kind: "axe", tier: 4 },
    placeable: false,
  },
  door: {
    name: "Door",
    color: "#9a6836",
  },
  fence: {
    name: "Fence",
    color: "#a97843",
  },
  furnace: {
    name: "Furnace",
    color: "#5c5f66",
  },
  chest: {
    name: "Chest",
    color: "#8c5a1e",
  },
};

const DOOR_BLOCK_COLORS = {
  door_bottom_closed: "#9a6836",
  door_top_closed: "#9a6837",
  door_bottom_open: "#9a6838",
  door_top_open: "#9a6839",
};

// Ore blocks only exist in generated terrain; mining one drops `drop`.
const ORE_BLOCKS = {
  coal_ore: {
    name: "Coal Ore",
    color: "#4b4e55",
    drop: "coal",
    minTier: 1,
    hardness: 2,
  },
  copper_ore: {
    name: "Copper Ore",
    color: "#a0805f",
    drop: "raw_copper",
    minTier: 2,
    hardness: 2.5,
  },
  iron_ore: {
    name: "Iron Ore",
    color: "#a89483",
    drop: "raw_iron",
    minTier: 3,
    hardness: 3,
  },
  gold_ore: {
    name: "Gold Ore",
    color: "#c9b24a",
    drop: "raw_gold",
    minTier: 4,
    hardness: 3.5,
  },
};

const TOOL_TIER_SPEED = [1, 1.6, 2.2, 3, 4];
const MIN_MINE_DURATION_MS = 150;

const CONTAINER_KINDS = ["furnace", "chest"];

const SMELT_TIME_MS = 5000;

const SMELTING_RECIPES = {
  raw_copper: "copper_ingot",
  raw_iron: "iron_ingot",
  raw_gold: "gold_ingot",
};

// Milliseconds of smelting a single fuel item provides.
const FUEL_BURN_MS = {
  coal: 40000,
  log: 10000,
  planks: 5000,
};

const FURNACE_SLOTS = {
  input: 0,
  fuel: 1,
  output: 2,
};

const CRAFTING_RECIPES = [
  {
    id: "planks",
    label: "4 Planks",
    ingredients: {
      log: 1,
    },
    output: {
      type: "planks",
      count: 4,
    },
  },
  {
    id: "sticks",
    label: "4 Sticks",
    ingredients: {
      planks: 2,
    },
    output: {
      type: "sticks",
      count: 4,
    },
  },
  {
    id: "wood_pickaxe",
    label: "Wood Pickaxe",
    ingredients: {
      planks: 3,
      sticks: 2,
    },
    output: {
      type: "wood_pickaxe",
      count: 1,
    },
  },
  {
    id: "stone_pickaxe",
    label: "Stone Pickaxe",
    ingredients: {
      stone: 3,
      sticks: 2,
    },
    output: {
      type: "stone_pickaxe",
      count: 1,
    },
  },
  {
    id: "copper_pickaxe",
    label: "Copper Pickaxe",
    ingredients: {
      copper_ingot: 3,
      sticks: 2,
    },
    output: {
      type: "copper_pickaxe",
      count: 1,
    },
  },
  {
    id: "iron_pickaxe",
    label: "Iron Pickaxe",
    ingredients: {
      iron_ingot: 3,
      sticks: 2,
    },
    output: {
      type: "iron_pickaxe",
      count: 1,
    },
  },
  {
    id: "wood_axe",
    label: "Wood Axe",
    ingredients: {
      planks: 3,
      sticks: 2,
    },
    output: {
      type: "wood_axe",
      count: 1,
    },
  },
  {
    id: "stone_axe",
    label: "Stone Axe",
    ingredients: {
      stone: 3,
      sticks: 2,
    },
    output: {
      type: "stone_axe",
      count: 1,
    },
  },
  {
    id: "copper_axe",
    label: "Copper Axe",
    ingredients: {
      copper_ingot: 3,
      sticks: 2,
    },
    output: {
      type: "copper_axe",
      count: 1,
    },
  },
  {
    id: "iron_axe",
    label: "Iron Axe",
    ingredients: {
      iron_ingot: 3,
      sticks: 2,
    },
    output: {
      type: "iron_axe",
      count: 1,
    },
  },
  {
    id: "door",
    label: "3 Doors",
    ingredients: {
      planks: 6,
    },
    output: {
      type: "door",
      count: 3,
    },
  },
  {
    id: "fence",
    label: "3 Fences",
    ingredients: {
      planks: 4,
      sticks: 2,
    },
    output: {
      type: "fence",
      count: 3,
    },
  },
  {
    id: "furnace",
    label: "Furnace",
    ingredients: {
      stone: 8,
    },
    output: {
      type: "furnace",
      count: 1,
    },
  },
  {
    id: "chest",
    label: "Chest",
    ingredients: {
      planks: 8,
    },
    output: {
      type: "chest",
      count: 1,
    },
  },
];

function itemTypeFromColor(color) {
  const normalizedColor = String(color || "").toLowerCase();

  for (const [type, definition] of Object.entries(
    ITEM_DEFINITIONS,
  )) {
    if (definition.color.toLowerCase() === normalizedColor) {
      return type;
    }
  }

  return `block:${normalizedColor}`;
}

// Items from older saves (or the server) may lack a type or carry an
// unknown one; fall back to the color so they migrate safely.
function resolveItemType(item) {
  if (
    typeof item?.type === "string" &&
    (ITEM_DEFINITIONS[item.type] ||
      /^block:#[0-9a-f]{6}$/.test(item.type))
  ) {
    return item.type;
  }

  return itemTypeFromColor(item?.color);
}

function worldBlockTypeFromColor(color) {
  const normalizedColor = String(color || "").toLowerCase();

  for (const [type, doorColor] of Object.entries(
    DOOR_BLOCK_COLORS,
  )) {
    if (doorColor === normalizedColor) {
      return type;
    }
  }

  for (const [type, ore] of Object.entries(ORE_BLOCKS)) {
    if (ore.color === normalizedColor) {
      return type;
    }
  }

  return itemTypeFromColor(normalizedColor);
}

function itemDisplayName(type) {
  return (
    ITEM_DEFINITIONS[type]?.name ||
    ORE_BLOCKS[type]?.name ||
    "Block"
  );
}

function isDoorBlock(block) {
  return Boolean(block?.type?.startsWith("door_"));
}

function isOpenDoorBlock(block) {
  return Boolean(block?.type?.endsWith("_open"));
}

function isContainerBlock(block) {
  return CONTAINER_KINDS.includes(block?.type);
}

// =============================================================================
// MINING TIERS
// =============================================================================

function toolOf(item) {
  if (!item) {
    return null;
  }

  return ITEM_DEFINITIONS[resolveItemType(item)]?.tool || null;
}

function blockProperties(block) {
  const type = block?.type || "";
  const ore = ORE_BLOCKS[type];

  if (ore) {
    return {
      tool: "pickaxe",
      minTier: ore.minTier,
      hardness: ore.hardness,
    };
  }

  if (type === "stone" || type === "furnace") {
    return { tool: "pickaxe", minTier: 0, hardness: 1.5 };
  }

  if (
    type === "log" ||
    type === "planks" ||
    type === "leaves" ||
    type === "fence" ||
    type === "chest" ||
    type.startsWith("door_")
  ) {
    return { tool: "axe", minTier: 0, hardness: 1 };
  }

  return { tool: null, minTier: 0, hardness: 1 };
}

function effectiveToolTier(item, properties) {
  const tool = toolOf(item);

  return tool && tool.kind === properties.tool ? tool.tier : 0;
}

function canHarvest(block, item) {
  const properties = blockProperties(block);

  return effectiveToolTier(item, properties) >= properties.minTier;
}

function requirementText(block) {
  const { minTier } = blockProperties(block);
  const toolType = `${TOOL_TIER_PREFIXES[minTier]}_pickaxe`;

  return `Requires ${itemDisplayName(toolType)} or better`;
}

function miningDurationMs(block, item) {
  const properties = blockProperties(block);
  const tier = effectiveToolTier(item, properties);

  return Math.max(
    MIN_MINE_DURATION_MS,
    (MINE_DURATION_MS * properties.hardness) /
      TOOL_TIER_SPEED[tier],
  );
}

function dropTypeForBlock(block) {
  return ORE_BLOCKS[block.type]?.drop || block.type;
}

function toolDescription(type) {
  const tool = ITEM_DEFINITIONS[type]?.tool;

  if (!tool) {
    return "";
  }

  if (tool.kind === "axe") {
    return `Axe tier ${tool.tier}: chops wood faster`;
  }

  const ores = Object.values(ORE_BLOCKS)
    .filter((ore) => ore.minTier <= tool.tier)
    .map((ore) => ore.name)
    .join(", ");

  return (
    `Pickaxe tier ${tool.tier}: mines faster` +
    (ores ? `; can harvest ${ores}` : "")
  );
}

function recipeNote(recipe) {
  const type = recipe.output.type;

  if (type === "furnace") {
    return "Place it, then click it to smelt ore";
  }

  if (type === "chest") {
    return "Place it, then click it to store items";
  }

  return toolDescription(type);
}

// =============================================================================
// WORLD STORAGE
// =============================================================================

const placedBlocks = new Map();
const blockEdits = new Map();

function blockKey(x, y, z) {
  return `${x},${y},${z}`;
}

function addPlacedBlock(
  x,
  y,
  z,
  color,
  type = itemTypeFromColor(color),
) {
  placedBlocks.set(blockKey(x, y, z), {
    x,
    y,
    z,
    color,
    type,
  });
}

// =============================================================================
// TREES
// =============================================================================

function hash2(x, y) {
  y = Math.imul(x, 374761393) + Math.imul(y, 668265263);
  y = Math.imul(y ^ (y >>> 13), 1274126177);

  return ((y ^ (y >>> 16)) >>> 0);
}

const treeAnchorCache = new Map();

function getTreeAnchor(cellX, cellZ) {
  const cacheKey = `${cellX},${cellZ}`;

  if (treeAnchorCache.has(cacheKey)) {
    return treeAnchorCache.get(cacheKey);
  }

  const hash = hash2(cellX, cellZ);

  if (hash % 2 !== 0) {
    treeAnchorCache.set(cacheKey, null);
    return null;
  }

  const anchor = {
    x: 12 * cellX + ((hash >>> 8) % 7) - 3,
    z: 12 * cellZ + ((hash >>> 16) % 7) - 3,
    height: 3 + ((hash >>> 24) % 3),
  };

  if (Math.hypot(anchor.x, anchor.z) < 8) {
    treeAnchorCache.set(cacheKey, null);
    return null;
  }

  treeAnchorCache.set(cacheKey, anchor);
  return anchor;
}

function generatedTreeBlock(x, y, z) {
  const cellX = Math.floor(x / 12);
  const cellZ = Math.floor(z / 12);

  for (let offsetX = cellX - 1; offsetX <= cellX + 1; offsetX += 1) {
    for (
      let offsetZ = cellZ - 1;
      offsetZ <= cellZ + 1;
      offsetZ += 1
    ) {
      const anchor = getTreeAnchor(offsetX, offsetZ);

      if (!anchor) continue;

      const groundY = terrainHeight(anchor.x, anchor.z);
      const treeTopY = groundY + anchor.height;

      if (
        x === anchor.x &&
        z === anchor.z &&
        y >= groundY &&
        y < treeTopY
      ) {
        return {
          x,
          y,
          z,
          color: ITEM_DEFINITIONS.log.color,
          type: "log",
        };
      }

      const distanceX = Math.abs(x - anchor.x);
      const distanceZ = Math.abs(z - anchor.z);
      const relativeY = y - treeTopY;

      if (
        relativeY >= 0 &&
        relativeY <= 2 &&
        distanceX <= 2 &&
        distanceZ <= 2 &&
        distanceX +
          distanceZ +
          Math.max(0, relativeY - 1) <=
          3 &&
        y >= terrainHeight(x, z)
      ) {
        return {
          x,
          y,
          z,
          color: ITEM_DEFINITIONS.leaves.color,
          type: "leaves",
        };
      }
    }
  }

  return null;
}

// =============================================================================
// CAVES AND ORES
// =============================================================================

// Caves never come closer to the surface than this many blocks, so they
// stay below trees and the terrain height model.
const CAVE_ROOF_THICKNESS = 5;
const STONE_TOP_Y = -5;
const TUNNEL_WIDTH = 0.075;
const CHAMBER_THRESHOLD = 0.78;

function hash3(x, y, z, salt) {
  let h = (WORLD_SEED ^ Math.imul(salt + 1, 0x9e3779b1)) | 0;

  h = Math.imul(h ^ x, 0x85ebca6b);
  h ^= h >>> 13;
  h = Math.imul(h ^ y, 0xc2b2ae35);
  h ^= h >>> 16;
  h = Math.imul(h ^ z, 0x27d4eb2f);
  h ^= h >>> 15;
  h = Math.imul(h, 0x165667b1);

  return (h ^ (h >>> 16)) >>> 0;
}

function valueNoise3(x, y, z, salt) {
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const z0 = Math.floor(z);
  const fx = x - x0;
  const fy = y - y0;
  const fz = z - z0;
  const u = fx * fx * (3 - 2 * fx);
  const v = fy * fy * (3 - 2 * fy);
  const w = fz * fz * (3 - 2 * fz);

  const corner = (dx, dy, dz) =>
    hash3(x0 + dx, y0 + dy, z0 + dz, salt) / 4294967296;

  return lerp(
    lerp(
      lerp(corner(0, 0, 0), corner(1, 0, 0), u),
      lerp(corner(0, 1, 0), corner(1, 1, 0), u),
      v,
    ),
    lerp(
      lerp(corner(0, 0, 1), corner(1, 0, 1), u),
      lerp(corner(0, 1, 1), corner(1, 1, 1), u),
      v,
    ),
    w,
  );
}

function isCaveCell(x, y, z, surface) {
  if (
    y < WORLD_MIN_Y + 2 ||
    y > surface - CAVE_ROOF_THICKNESS
  ) {
    return false;
  }

  if (valueNoise3(x / 24, y / 12, z / 24, 3) > CHAMBER_THRESHOLD) {
    return true;
  }

  const first = valueNoise3(x / 16, y / 9, z / 16, 1);

  if (Math.abs(first - 0.5) > TUNNEL_WIDTH) {
    return false;
  }

  const second = valueNoise3(x / 16, y / 9, z / 16, 2);

  return Math.abs(second - 0.5) <= TUNNEL_WIDTH;
}

const ORE_CELL_SIZE = [6, 4, 6];

// Ore deposits are small blobs: each 6x4x6 cell may hold one deposit whose
// type depends on a hash of the cell and on its depth.
function oreTypeAt(x, y, z) {
  if (y > STONE_TOP_Y) {
    return null;
  }

  const cellX = Math.floor(x / ORE_CELL_SIZE[0]);
  const cellY = Math.floor(y / ORE_CELL_SIZE[1]);
  const cellZ = Math.floor(z / ORE_CELL_SIZE[2]);
  const hash = hash3(cellX, cellY, cellZ, 11);
  const roll = hash % 100;
  const midY = cellY * ORE_CELL_SIZE[1] + 2;

  let type = null;

  if (roll < 4 && midY <= -14) {
    type = "gold_ore";
  } else if (roll < 12 && midY <= -10) {
    type = "iron_ore";
  } else if (roll < 24) {
    type = "copper_ore";
  } else if (roll < 44) {
    type = "coal_ore";
  }

  if (!type) {
    return null;
  }

  const centerX =
    cellX * ORE_CELL_SIZE[0] + 1 + ((hash >>> 8) % 4);
  const centerY =
    cellY * ORE_CELL_SIZE[1] + 1 + ((hash >>> 12) % 2);
  const centerZ =
    cellZ * ORE_CELL_SIZE[2] + 1 + ((hash >>> 16) % 4);

  const distance =
    (x - centerX) ** 2 +
    (y - centerY) ** 2 +
    (z - centerZ) ** 2;

  if (distance > 3 || hash3(x, y, z, 12) % 100 >= 80) {
    return null;
  }

  return type;
}

const generatedBlockCache = new Map();

function generateTerrainBlock(x, y, z, surface) {
  if (isCaveCell(x, y, z, surface)) {
    return null;
  }

  const oreType = oreTypeAt(x, y, z);

  if (oreType) {
    return {
      x,
      y,
      z,
      color: ORE_BLOCKS[oreType].color,
      type: oreType,
    };
  }

  const isStone = y <= STONE_TOP_Y;

  return {
    x,
    y,
    z,
    color: isStone
      ? ITEM_DEFINITIONS.stone.color
      : terrainColor(y),
    type: isStone ? "stone" : "dirt",
  };
}

function getTerrainBlock(x, y, z, surface) {
  const key = blockKey(x, y, z);
  let block = generatedBlockCache.get(key);

  if (block === undefined) {
    if (generatedBlockCache.size > 250000) {
      generatedBlockCache.clear();
    }

    block = generateTerrainBlock(x, y, z, surface);
    generatedBlockCache.set(key, block);
  }

  return block;
}

function getBlock(x, y, z) {
  const key = blockKey(x, y, z);

  if (blockEdits.has(key)) {
    const editedBlock = blockEdits.get(key);

    if (editedBlock && !editedBlock.type) {
      editedBlock.type = worldBlockTypeFromColor(
        editedBlock.color,
      );
    }

    return editedBlock;
  }

  if (placedBlocks.has(key)) {
    const placedBlock = placedBlocks.get(key);

    if (!placedBlock.type) {
      placedBlock.type = worldBlockTypeFromColor(
        placedBlock.color,
      );
    }

    return placedBlock;
  }

  const surface = terrainHeight(x, z);

  if (y >= WORLD_MIN_Y && y < surface) {
    return getTerrainBlock(x, y, z, surface);
  }

  return generatedTreeBlock(x, y, z);
}

function isSolid(x, y, z) {
  const block = getBlock(x, y, z);

  return Boolean(block && !isOpenDoorBlock(block));
}

function isFullCubeBlock(x, y, z) {
  const block = getBlock(x, y, z);

  return Boolean(
    block &&
      isSolid(x, y, z) &&
      !isDoorBlock(block),
  );
}

function removeBlock(x, y, z) {
  const key = blockKey(x, y, z);

  blockEdits.set(key, null);
  placedBlocks.delete(key);

  sendWorldEdit(x, y, z, null);
}

function writeWorldBlock(x, y, z, color, type) {
  const block = {
    x,
    y,
    z,
    color,
    type,
  };

  blockEdits.set(blockKey(x, y, z), block);
  sendWorldEdit(x, y, z, color);
}

// Example blocks.
addPlacedBlock(-3, terrainHeight(-3, 0), 0, "#d84838");
addPlacedBlock(-1, terrainHeight(-1, 0), 0, "#37a84d");
addPlacedBlock(1, terrainHeight(1, 0), 0, "#397bd7");

// =============================================================================
// DOORS
// =============================================================================

function getDoorBottomY(y, block) {
  return block?.type?.startsWith("door_top_") ? y - 1 : y;
}

function getDoorPair(x, y, z) {
  const block = getBlock(x, y, z);

  if (!isDoorBlock(block)) {
    return null;
  }

  const bottomY = getDoorBottomY(y, block);
  const bottom = getBlock(x, bottomY, z);
  const top = getBlock(x, bottomY + 1, z);

  if (!isDoorBlock(bottom) || !isDoorBlock(top)) {
    return null;
  }

  return {
    bottomY,
    bottom,
    top,
  };
}

function toggleDoorAtHit(hit) {
  if (!hit) {
    return false;
  }

  const [x, y, z] = hit.hit;
  const doorPair = getDoorPair(x, y, z);

  if (!doorPair) {
    return false;
  }

  const open = !isOpenDoorBlock(doorPair.bottom);

  const bottomType = open
    ? "door_bottom_open"
    : "door_bottom_closed";

  const topType = open
    ? "door_top_open"
    : "door_top_closed";

  writeWorldBlock(
    x,
    doorPair.bottomY,
    z,
    DOOR_BLOCK_COLORS[bottomType],
    bottomType,
  );

  writeWorldBlock(
    x,
    doorPair.bottomY + 1,
    z,
    DOOR_BLOCK_COLORS[topType],
    topType,
  );

  return true;
}

function toggleTargetedDoor() {
  return toggleDoorAtHit(raycast());
}

function breakBlockAt(x, y, z) {
  const block = getBlock(x, y, z);

  if (!block) {
    return false;
  }

  if (isDoorBlock(block)) {
    const doorPair = getDoorPair(x, y, z);

    if (!doorPair) {
      return false;
    }

    if (
      !addToInventory(
        ITEM_DEFINITIONS.door.color,
        "door",
      )
    ) {
      setStatus("Inventory full — make room first.");
      return false;
    }

    removeBlock(x, doorPair.bottomY, z);
    removeBlock(x, doorPair.bottomY + 1, z);

    return true;
  }

  if (isContainerBlock(block)) {
    const container = containers.get(blockKey(x, y, z));

    if (container && !containerIsEmpty(container)) {
      setStatus(
        `Empty the ${itemDisplayName(block.type)} before breaking it.`,
      );
      return false;
    }
  }

  const dropType = dropTypeForBlock(block);

  if (
    !addToInventory(
      ITEM_DEFINITIONS[dropType]?.color || block.color,
      dropType,
    )
  ) {
    setStatus("Inventory full — make room first.");
    return false;
  }

  if (isContainerBlock(block)) {
    containers.delete(blockKey(x, y, z));
    containersDirty = true;

    if (openContainerKey === blockKey(x, y, z)) {
      closeContainer();
    }
  }

  removeBlock(x, y, z);
  return true;
}

// =============================================================================
// CAMERA
// =============================================================================

class Camera {
  constructor(x, y, z) {
    this.pos = [x, y, z];
    this.rot = [0, 0];
    this.velocityY = 0;
    this.grounded = true;
  }

  mouseMove(deltaX, deltaY) {
    this.rot[1] += deltaX / 200;
    this.rot[0] -= deltaY / 200;

    const limit = Math.PI / 2 - 0.01;

    this.rot[0] = Math.max(
      -limit,
      Math.min(limit, this.rot[0]),
    );
  }
}

const camera = new Camera(
  0,
  terrainHeight(0, -10),
  -10,
);

// =============================================================================
// INPUT AND GAME STATE
// =============================================================================

const inventory = Array.from({ length: 27 }, () => null);
const keys = Object.create(null);
const remotePlayers = new Map();
const pendingWorldEdits = new Map();

let selectedSlot = 0;
let inventoryOpen = false;
let jumpRequested = false;

let gamepadMoveX = 0;
let gamepadMoveY = 0;
let gamepadLookX = 0;
let gamepadLookY = 0;

let touchMoveX = 0;
let touchMoveY = 0;
let touchLookX = 0;
let touchLookY = 0;

let gamepadInventoryCursor = 0;
let gamepadDragSource = null;

const miningSources = new Set();

let miningTargetKey = null;
let miningStartedAt = 0;
let lastSuccessfulPlacementAt = -Infinity;

let worldSocket = null;
let localPlayerId = null;
let lastNetworkUpdate = 0;
let hasLoadedServerState = false;
let inventoryDirty = false;

const previousPadActions = {
  jump: false,
  mine: false,
  place: false,
  inventory: false,
  back: false,
  nextSlot: false,
  dpadUp: false,
  dpadDown: false,
  dpadLeft: false,
  dpadRight: false,
};

// =============================================================================
// INVENTORY
// =============================================================================

function inventoryPayload() {
  return inventory.map((item) =>
    item
      ? {
          type: resolveItemType(item),
          color: item.color,
          count: item.count,
        }
      : null,
  );
}

function syncInventory() {
  inventoryDirty = true;

  if (
    hasLoadedServerState &&
    worldSocket &&
    worldSocket.readyState === WebSocket.OPEN
  ) {
    worldSocket.send(
      JSON.stringify({
        type: "inventory",
        inventory: inventoryPayload(),
      }),
    );
  }
}

function addToInventory(
  color,
  type = itemTypeFromColor(color),
) {
  let slotIndex = inventory.findIndex(
    (item) =>
      item &&
      (resolveItemType(item)) === type &&
      item.count < 64,
  );

  if (slotIndex < 0) {
    slotIndex = inventory.findIndex((item) => !item);
  }

  if (slotIndex < 0) {
    return false;
  }

  const itemColor = ITEM_DEFINITIONS[type]?.color || color;

  if (!inventory[slotIndex]) {
    inventory[slotIndex] = {
      type,
      color: itemColor,
      count: 0,
    };
  }

  inventory[slotIndex].count += 1;

  renderInventory();
  syncInventory();

  return true;
}

function countInventoryItem(type) {
  return inventory.reduce((total, item) => {
    if (!item) {
      return total;
    }

    const itemType =
      resolveItemType(item);

    return total + (itemType === type ? item.count : 0);
  }, 0);
}

function countItemsIn(items, type) {
  return items.reduce((total, item) => {
    if (!item) {
      return total;
    }

    const itemType =
      resolveItemType(item);

    return total + (itemType === type ? item.count : 0);
  }, 0);
}

function hasRecipeIngredients(recipe) {
  return Object.entries(recipe.ingredients).every(
    ([type, count]) => countInventoryItem(type) >= count,
  );
}

function cloneInventory() {
  return inventory.map((item) => (item ? { ...item } : null));
}

function consumeIngredientsFrom(items, ingredients) {
  for (const [type, requiredCount] of Object.entries(
    ingredients,
  )) {
    let remaining = requiredCount;

    for (
      let index = 0;
      index < items.length && remaining > 0;
      index += 1
    ) {
      const item = items[index];

      if (
        !item ||
        (resolveItemType(item)) !== type
      ) {
        continue;
      }

      const amount = Math.min(item.count, remaining);

      item.count -= amount;
      remaining -= amount;

      if (item.count <= 0) {
        items[index] = null;
      }
    }

    if (remaining > 0) {
      return false;
    }
  }

  return true;
}

function addCraftedItemTo(items, type, count) {
  const definition = ITEM_DEFINITIONS[type];

  if (!definition) {
    return false;
  }

  let remaining = count;

  for (
    let index = 0;
    index < items.length && remaining > 0;
    index += 1
  ) {
    const item = items[index];

    if (
      !item ||
      (resolveItemType(item)) !== type ||
      item.count >= 64
    ) {
      continue;
    }

    const amount = Math.min(64 - item.count, remaining);

    item.count += amount;
    remaining -= amount;
  }

  while (remaining > 0) {
    const emptyIndex = items.findIndex((item) => !item);

    if (emptyIndex < 0) {
      return false;
    }

    const amount = Math.min(64, remaining);

    items[emptyIndex] = {
      type,
      color: definition.color,
      count: amount,
    };

    remaining -= amount;
  }

  return true;
}

function craftRecipe(recipe) {
  const nextInventory = cloneInventory();

  if (!consumeIngredientsFrom(nextInventory, recipe.ingredients)) {
    craftStatusElement.textContent = "Not enough materials.";
    return;
  }

  if (
    !addCraftedItemTo(
      nextInventory,
      recipe.output.type,
      recipe.output.count,
    )
  ) {
    craftStatusElement.textContent =
      "Make room in your inventory first.";
    return;
  }

  for (let index = 0; index < inventory.length; index += 1) {
    inventory[index] = nextInventory[index];
  }

  craftStatusElement.textContent =
    `Crafted ${recipe.output.count} ` +
    `${itemDisplayName(recipe.output.type)}.`;

  renderInventory();
  syncInventory();
}

function renderCraftingRecipes() {
  craftingRecipesElement.replaceChildren();

  const tierInfo = document.createElement("p");

  tierInfo.className = "tierInfo";
  tierInfo.textContent =
    "Mining tiers — " +
    Object.values(ORE_BLOCKS)
      .map(
        (ore) =>
          `${ore.name}: ${itemDisplayName(
            `${TOOL_TIER_PREFIXES[ore.minTier]}_pickaxe`,
          )}`,
      )
      .join(" · ") +
    ". Smelt raw ore in a furnace to get ingots for copper and iron tools.";
  craftingRecipesElement.appendChild(tierInfo);

  for (const recipe of CRAFTING_RECIPES) {
    const ingredients = Object.entries(recipe.ingredients)
      .map(
        ([type, count]) =>
          `${count} ${itemDisplayName(type)}`,
      )
      .join(" + ");

    const button = document.createElement("button");

    button.type = "button";
    button.className = "craftButton";
    button.textContent = `${recipe.label} — ${ingredients}`;
    button.disabled = !hasRecipeIngredients(recipe);

    const note = recipeNote(recipe);

    if (note) {
      const noteElement = document.createElement("span");

      noteElement.className = "craftNote";
      noteElement.textContent = note;
      button.appendChild(noteElement);
    }

    button.addEventListener("click", () => {
      craftRecipe(recipe);
    });

    craftingRecipesElement.appendChild(button);
  }
}

function makeSlot(index) {
  const item = inventory[index];
  const slot = document.createElement("div");

  slot.className = "slot";

  if (index === selectedSlot) {
    slot.classList.add("selected");
  }

  if (index === gamepadInventoryCursor) {
    slot.classList.add("gamepad-cursor");
  }

  slot.draggable = true;
  slot.title = item
    ? `Slot ${index + 1}: ` +
      `${itemDisplayName(resolveItemType(item))} ` +
      `(${item.count})` +
      (toolDescription(resolveItemType(item))
        ? ` — ${toolDescription(resolveItemType(item))}`
        : "")
    : `Slot ${index + 1}`;

  const slotNumber = document.createElement("span");

  slotNumber.className = "slotNumber";
  slotNumber.textContent = index < 9 ? String(index + 1) : "";

  slot.appendChild(slotNumber);

  if (item && item.count > 0) {
    const slotColor = document.createElement("span");

    slotColor.className = "slotColor";
    slotColor.style.backgroundColor = item.color;

    slot.appendChild(slotColor);

    const slotCount = document.createElement("span");

    slotCount.className = "slotCount";
    slotCount.textContent = String(item.count);

    slot.appendChild(slotCount);
  }

  slot.addEventListener("click", () => {
    if (openContainerKey && inventoryOpen) {
      moveInventoryToContainer(index);
      return;
    }

    if (index < 9) {
      selectedSlot = index;
      gamepadInventoryCursor = index;
      renderInventory();
      return;
    }

    if (inventoryOpen && inventory[index]) {
      [
        inventory[selectedSlot],
        inventory[index],
      ] = [
        inventory[index],
        inventory[selectedSlot],
      ];

      renderInventory();
      syncInventory();
    }
  });

  slot.addEventListener("dragstart", (event) => {
    event.dataTransfer.setData(
      "text/plain",
      String(index),
    );
  });

  slot.addEventListener("dragover", (event) => {
    event.preventDefault();
  });

  slot.addEventListener("drop", (event) => {
    event.preventDefault();

    const data = event.dataTransfer.getData("text/plain");

    if (data.startsWith("c:")) {
      dropContainerStackOnInventory(data, index);
      return;
    }

    const sourceIndex = Number(data);

    if (
      !Number.isInteger(sourceIndex) ||
      sourceIndex < 0 ||
      sourceIndex >= inventory.length ||
      sourceIndex === index
    ) {
      return;
    }

    [
      inventory[sourceIndex],
      inventory[index],
    ] = [
      inventory[index],
      inventory[sourceIndex],
    ];

    renderInventory();
    syncInventory();
  });

  return slot;
}

function renderInventory() {
  hotbarElement.replaceChildren();
  inventoryGrid.replaceChildren();

  for (let index = 0; index < inventory.length; index += 1) {
    const slot = makeSlot(index);

    if (index < 9) {
      hotbarElement.appendChild(slot);
    }

    inventoryGrid.appendChild(makeSlot(index));
  }

  renderCraftingRecipes();
  renderContainerPanel();
}

// =============================================================================
// STATUS MESSAGES
// =============================================================================

let statusTimer = null;
let statusExpiresAt = 0;

function setStatus(message) {
  if (!statusElement) {
    return;
  }

  const now = performance.now();

  if (
    statusElement.textContent === message &&
    statusExpiresAt - now > 1500
  ) {
    return;
  }

  statusElement.textContent = message;
  statusExpiresAt = now + 3000;

  window.clearTimeout(statusTimer);
  statusTimer = window.setTimeout(() => {
    statusElement.textContent = "";
  }, 3000);
}

// =============================================================================
// STACK TRANSFERS
// =============================================================================

// Moves as much of `source[sourceIndex]` as fits into `target`, merging into
// matching stacks first. Counts are conserved: whatever does not fit stays
// in the source slot. Returns the number of items moved.
function moveStack(
  source,
  sourceIndex,
  target,
  accepts = () => true,
) {
  const item = source[sourceIndex];

  if (!item || item.count <= 0) {
    return 0;
  }

  const type = resolveItemType(item);
  const startCount = item.count;

  for (
    let index = 0;
    index < target.length && item.count > 0;
    index += 1
  ) {
    const existing = target[index];

    if (
      !existing ||
      resolveItemType(existing) !== type ||
      existing.count >= MAX_STACK ||
      !accepts(index, item)
    ) {
      continue;
    }

    const amount = Math.min(MAX_STACK - existing.count, item.count);

    existing.count += amount;
    item.count -= amount;
  }

  for (
    let index = 0;
    index < target.length && item.count > 0;
    index += 1
  ) {
    if (target[index] || !accepts(index, item)) {
      continue;
    }

    const amount = Math.min(MAX_STACK, item.count);

    target[index] = { type, color: item.color, count: amount };
    item.count -= amount;
  }

  if (item.count <= 0) {
    source[sourceIndex] = null;
  }

  return startCount - item.count;
}

// Moves a stack onto a specific slot: into an empty slot, merged into a
// matching stack, or swapped with a different stack when both sides allow it.
function moveStackToSlot(
  source,
  sourceIndex,
  target,
  targetIndex,
  targetAccepts = () => true,
  sourceAccepts = () => true,
) {
  const item = source[sourceIndex];

  if (
    !item ||
    item.count <= 0 ||
    (source === target && sourceIndex === targetIndex) ||
    !targetAccepts(targetIndex, item)
  ) {
    return 0;
  }

  const destination = target[targetIndex];

  if (!destination) {
    target[targetIndex] = item;
    source[sourceIndex] = null;
    return item.count;
  }

  if (resolveItemType(destination) === resolveItemType(item)) {
    const amount = Math.min(
      MAX_STACK - destination.count,
      item.count,
    );

    destination.count += amount;
    item.count -= amount;

    if (item.count <= 0) {
      source[sourceIndex] = null;
    }

    return amount;
  }

  if (!sourceAccepts(sourceIndex, destination)) {
    return 0;
  }

  target[targetIndex] = item;
  source[sourceIndex] = destination;

  return item.count;
}

// =============================================================================
// FURNACES AND CHESTS
// =============================================================================

const containers = new Map();

let openContainerKey = null;
let containersDirty = false;
let lastContainerSave = 0;
let lastFurnaceTick = Date.now();
let furnaceProgressElement = null;
let furnaceInfoElement = null;
let renderedContainerSignature = "";

function createContainer(kind) {
  return {
    kind,
    slots: Array.from(
      { length: kind === "chest" ? 27 : 3 },
      () => null,
    ),
    burn: 0,
    progress: 0,
  };
}

function containerAccepts(container, slotIndex, item) {
  if (container.kind === "chest") {
    return true;
  }

  const type = resolveItemType(item);

  if (slotIndex === FURNACE_SLOTS.input) {
    return Boolean(SMELTING_RECIPES[type]);
  }

  if (slotIndex === FURNACE_SLOTS.fuel) {
    return Boolean(FUEL_BURN_MS[type]);
  }

  return false;
}

function containerIsEmpty(container) {
  return container.slots.every((item) => !item);
}

function furnaceOutputFor(furnace) {
  const input = furnace.slots[FURNACE_SLOTS.input];

  if (!input) {
    return null;
  }

  const outputType = SMELTING_RECIPES[resolveItemType(input)];
  const output = furnace.slots[FURNACE_SLOTS.output];

  if (
    !outputType ||
    (output &&
      (resolveItemType(output) !== outputType ||
        output.count >= MAX_STACK))
  ) {
    return null;
  }

  return outputType;
}

// Advances a furnace by `elapsedMs`. Fuel is lit only when smelting needs it
// and burns only while smelting, so results depend solely on the contents.
function tickFurnace(furnace, elapsedMs) {
  let remaining = Math.max(0, Number(elapsedMs) || 0);
  let changed = false;

  while (remaining > 1e-9) {
    const outputType = furnaceOutputFor(furnace);

    if (!outputType) {
      if (furnace.progress !== 0) {
        furnace.progress = 0;
        changed = true;
      }

      break;
    }

    if (furnace.burn <= 1e-9) {
      const fuel = furnace.slots[FURNACE_SLOTS.fuel];
      const burnTime = fuel
        ? FUEL_BURN_MS[resolveItemType(fuel)]
        : 0;

      if (!burnTime) {
        break;
      }

      fuel.count -= 1;

      if (fuel.count <= 0) {
        furnace.slots[FURNACE_SLOTS.fuel] = null;
      }

      furnace.burn = burnTime;
      changed = true;
    }

    const step = Math.min(
      remaining,
      furnace.burn,
      SMELT_TIME_MS - furnace.progress,
    );

    furnace.burn -= step;
    furnace.progress += step;
    remaining -= step;
    changed = true;

    if (furnace.progress >= SMELT_TIME_MS - 1e-9) {
      const input = furnace.slots[FURNACE_SLOTS.input];
      const output = furnace.slots[FURNACE_SLOTS.output];

      input.count -= 1;

      if (input.count <= 0) {
        furnace.slots[FURNACE_SLOTS.input] = null;
      }

      if (output) {
        output.count += 1;
      } else {
        furnace.slots[FURNACE_SLOTS.output] = {
          type: outputType,
          color: ITEM_DEFINITIONS[outputType].color,
          count: 1,
        };
      }

      furnace.progress = 0;
    }
  }

  return changed;
}

function sanitizeStoredItem(item) {
  const type = resolveItemType(item);
  const definition = ITEM_DEFINITIONS[type];

  if (
    !definition ||
    !Number.isInteger(item?.count) ||
    item.count < 1 ||
    item.count > MAX_STACK
  ) {
    return null;
  }

  return { type, color: definition.color, count: item.count };
}

function serializeContainers() {
  const data = {};

  for (const [key, container] of containers) {
    data[key] = {
      kind: container.kind,
      slots: container.slots.map((item) =>
        item
          ? { type: resolveItemType(item), count: item.count }
          : null,
      ),
      burn: container.burn,
      progress: container.progress,
    };
  }

  return JSON.stringify({ version: 1, savedAt: Date.now(), data });
}

function restoreContainers(text, now = Date.now()) {
  containers.clear();

  let parsed;

  try {
    parsed = JSON.parse(text);
  } catch {
    return;
  }

  if (!parsed || typeof parsed.data !== "object" || !parsed.data) {
    return;
  }

  const elapsed = Math.max(0, now - (Number(parsed.savedAt) || now));

  for (const [key, saved] of Object.entries(parsed.data)) {
    if (
      !/^-?\d+,-?\d+,-?\d+$/.test(key) ||
      !CONTAINER_KINDS.includes(saved?.kind)
    ) {
      continue;
    }

    const container = createContainer(saved.kind);

    for (
      let index = 0;
      index < container.slots.length;
      index += 1
    ) {
      container.slots[index] = sanitizeStoredItem(
        saved.slots?.[index],
      );
    }

    if (container.kind === "furnace") {
      container.burn = Math.max(0, Number(saved.burn) || 0);
      container.progress = Math.min(
        SMELT_TIME_MS - 1,
        Math.max(0, Number(saved.progress) || 0),
      );

      tickFurnace(container, elapsed);
    }

    containers.set(key, container);
  }
}

function containerStorageKey() {
  return `voxelGame.containers.v1.${roomName}`;
}

function saveContainers() {
  containersDirty = false;
  lastContainerSave = performance.now();

  try {
    window.localStorage.setItem(
      containerStorageKey(),
      serializeContainers(),
    );
  } catch {
    setStatus(
      "Could not save furnace/chest contents in this browser.",
    );
  }
}

function loadContainers() {
  try {
    const text = window.localStorage.getItem(
      containerStorageKey(),
    );

    if (text) {
      restoreContainers(text);
    }
  } catch {
    // Local storage may be unavailable; containers then stay in memory.
  }
}

function ensureContainer(x, y, z, kind) {
  const key = blockKey(x, y, z);
  const existing = containers.get(key);

  if (existing && existing.kind === kind) {
    return existing;
  }

  if (existing && !containerIsEmpty(existing)) {
    return existing;
  }

  const container = createContainer(kind);

  containers.set(key, container);
  containersDirty = true;

  return container;
}

function getOpenContainer() {
  return openContainerKey ? containers.get(openContainerKey) : null;
}

function updateFurnaces() {
  const now = Date.now();
  const elapsed = now - lastFurnaceTick;

  lastFurnaceTick = now;

  for (const container of containers.values()) {
    if (
      container.kind === "furnace" &&
      tickFurnace(container, elapsed)
    ) {
      containersDirty = true;
    }
  }

  if (openContainerKey) {
    const [x, y, z] = openContainerKey.split(",").map(Number);
    const container = containers.get(openContainerKey);

    if (
      !container ||
      getBlock(x, y, z)?.type !== container.kind
    ) {
      closeContainer();
    } else if (
      containerSignature(container) !== renderedContainerSignature
    ) {
      renderContainerPanel();
    } else {
      updateFurnaceProgress(container);
    }
  }

  if (containersDirty && performance.now() - lastContainerSave > 2000) {
    saveContainers();
  }
}

function containerSignature(container) {
  return container.slots
    .map((item) =>
      item ? `${resolveItemType(item)}:${item.count}` : "-",
    )
    .join("|");
}

function updateFurnaceProgress(container) {
  if (!furnaceProgressElement || container.kind !== "furnace") {
    return;
  }

  furnaceProgressElement.value = container.progress;

  if (furnaceInfoElement) {
    furnaceInfoElement.textContent =
      container.burn > 0
        ? `Burning: ${Math.ceil(container.burn / 1000)}s of fuel lit`
        : "Not burning";
  }
}

function afterContainerChange() {
  containersDirty = true;
  saveContainers();
  renderInventory();
  syncInventory();
}

function openContainerAt(x, y, z) {
  const block = getBlock(x, y, z);

  if (!isContainerBlock(block)) {
    return false;
  }

  ensureContainer(x, y, z, block.type);

  setInventoryOpen(true);
  openContainerKey = blockKey(x, y, z);

  renderInventory();
  setStatus(`Opened ${itemDisplayName(block.type)}.`);

  return true;
}

function closeContainer() {
  openContainerKey = null;
  renderContainerPanel();
}

function containerFullMessage(container) {
  return container.kind === "furnace"
    ? "Furnace takes raw ore as input and coal, wood or planks as fuel."
    : "Chest is full.";
}

function moveInventoryToContainer(index) {
  const container = getOpenContainer();
  const item = inventory[index];

  if (!container || !item) {
    return;
  }

  const total = item.count;
  const moved = moveStack(
    inventory,
    index,
    container.slots,
    (slotIndex, candidate) =>
      containerAccepts(container, slotIndex, candidate),
  );

  if (moved === 0) {
    setStatus(containerFullMessage(container));
    return;
  }

  if (moved < total) {
    setStatus(`Only moved ${moved} of ${total}.`);
  }

  afterContainerChange();
}

function moveContainerToInventory(slotIndex) {
  const container = getOpenContainer();
  const item = container?.slots[slotIndex];

  if (!item) {
    return;
  }

  const total = item.count;
  const moved = moveStack(container.slots, slotIndex, inventory);

  if (moved === 0) {
    setStatus("Inventory full — make room first.");
    return;
  }

  if (moved < total) {
    setStatus(
      `Inventory full — took ${moved} of ${total}; the rest stays.`,
    );
  }

  afterContainerChange();
}

function takeAllFromContainer() {
  const container = getOpenContainer();

  if (!container) {
    return;
  }

  let left = 0;

  for (let index = 0; index < container.slots.length; index += 1) {
    if (container.slots[index]) {
      moveStack(container.slots, index, inventory);

      if (container.slots[index]) {
        left += 1;
      }
    }
  }

  setStatus(
    left > 0
      ? "Inventory full — some items stay in the container."
      : "Took everything.",
  );

  afterContainerChange();
}

function dropOnContainerSlot(data, targetIndex) {
  const container = getOpenContainer();

  if (!container) {
    return;
  }

  const accepts = (slotIndex, item) =>
    containerAccepts(container, slotIndex, item);
  let moved = 0;

  if (data.startsWith("c:")) {
    const sourceIndex = Number(data.slice(2));

    if (!Number.isInteger(sourceIndex)) {
      return;
    }

    moved = moveStackToSlot(
      container.slots,
      sourceIndex,
      container.slots,
      targetIndex,
      accepts,
      accepts,
    );
  } else {
    const sourceIndex = Number(data);

    if (!Number.isInteger(sourceIndex)) {
      return;
    }

    moved = moveStackToSlot(
      inventory,
      sourceIndex,
      container.slots,
      targetIndex,
      accepts,
    );
  }

  if (moved === 0) {
    setStatus(containerFullMessage(container));
    return;
  }

  afterContainerChange();
}

function dropContainerStackOnInventory(data, targetIndex) {
  const container = getOpenContainer();
  const sourceIndex = Number(data.slice(2));

  if (!container || !Number.isInteger(sourceIndex)) {
    return;
  }

  const moved = moveStackToSlot(
    container.slots,
    sourceIndex,
    inventory,
    targetIndex,
    () => true,
    (slotIndex, candidate) =>
      containerAccepts(container, slotIndex, candidate),
  );

  if (moved === 0) {
    setStatus("That slot can't take that item.");
    return;
  }

  afterContainerChange();
}

function makeContainerSlot(container, index, label) {
  const item = container.slots[index];
  const slot = document.createElement("div");

  slot.className = "slot";
  slot.draggable = true;
  slot.title = item
    ? `${itemDisplayName(resolveItemType(item))} (${item.count}) — ` +
      "click to move to your inventory"
    : label || `Slot ${index + 1}`;

  if (label) {
    const labelElement = document.createElement("span");

    labelElement.className = "slotLabel";
    labelElement.textContent = label;
    slot.appendChild(labelElement);
  }

  if (item && item.count > 0) {
    const color = document.createElement("span");

    color.className = "slotColor";
    color.style.backgroundColor = item.color;
    slot.appendChild(color);

    const count = document.createElement("span");

    count.className = "slotCount";
    count.textContent = String(item.count);
    slot.appendChild(count);
  }

  slot.addEventListener("click", () => {
    moveContainerToInventory(index);
  });

  slot.addEventListener("dragstart", (event) => {
    event.dataTransfer.setData("text/plain", `c:${index}`);
  });

  slot.addEventListener("dragover", (event) => {
    event.preventDefault();
  });

  slot.addEventListener("drop", (event) => {
    event.preventDefault();
    dropOnContainerSlot(
      event.dataTransfer.getData("text/plain"),
      index,
    );
  });

  return slot;
}

function renderContainerPanel() {
  furnaceProgressElement = null;
  furnaceInfoElement = null;

  if (!containerPanel) {
    return;
  }

  const container = getOpenContainer();

  containerPanel.hidden = !container;
  containerGrid.replaceChildren();
  containerGrid.classList.remove("furnace");

  if (!container) {
    renderedContainerSignature = "";
    return;
  }

  renderedContainerSignature = containerSignature(container);

  containerTitleElement.textContent =
    container.kind === "furnace" ? "Furnace" : "Chest";

  if (container.kind === "furnace") {
    containerGrid.classList.add("furnace");

    ["Input", "Fuel", "Output"].forEach((label, index) => {
      containerGrid.appendChild(
        makeContainerSlot(container, index, label),
      );
    });

    const progress = document.createElement("div");

    progress.className = "furnaceProgress";

    furnaceProgressElement = document.createElement("progress");
    furnaceProgressElement.max = SMELT_TIME_MS;

    furnaceInfoElement = document.createElement("div");

    progress.append(furnaceProgressElement, furnaceInfoElement);
    containerGrid.appendChild(progress);

    updateFurnaceProgress(container);

    containerInfoElement.textContent =
      "Input: raw copper/iron/gold. Fuel: coal, wood or planks. " +
      "Click a stack to move it; take ingots from Output. " +
      "Contents are saved in this browser only.";
  } else {
    for (let index = 0; index < container.slots.length; index += 1) {
      containerGrid.appendChild(makeContainerSlot(container, index));
    }

    containerInfoElement.textContent =
      "Click an inventory stack to store it, or a chest stack to take " +
      "it. Drag to choose a slot. Contents are saved in this browser only.";
  }
}

// =============================================================================
// UI STATE
// =============================================================================

function updateCoordinates() {
  const [x, y, z] = camera.pos;

  coordinatesElement.textContent =
    `X ${x.toFixed(1)} · ` +
    `Y ${y.toFixed(1)} · ` +
    `Z ${z.toFixed(1)}`;
}

function setInventoryOpen(open) {
  inventoryOpen = Boolean(open);

  inventoryPanel.classList.toggle("open", inventoryOpen);

  if (!inventoryOpen && openContainerKey) {
    closeContainer();
  }

  for (const key of Object.keys(keys)) {
    keys[key] = false;
  }

  jumpRequested = false;

  if (inventoryOpen) {
    stopMining();

    if (document.pointerLockElement === canvas) {
      document.exitPointerLock?.();
    }
  }
}

// =============================================================================
// NETWORKING
// =============================================================================

const requestedRoom =
  new URLSearchParams(window.location.search).get("room") ||
  "lobby";

const roomName = /^[a-zA-Z0-9_-]{1,48}$/.test(
  requestedRoom,
)
  ? requestedRoom
  : "lobby";

const websocketScheme =
  window.location.protocol === "https:" ? "wss:" : "ws:";

const socketUrl =
  `${websocketScheme}//${window.location.host}/ws/world/${roomName}/`;

function sendPlayerPosition() {
  if (
    hasLoadedServerState &&
    worldSocket &&
    worldSocket.readyState === WebSocket.OPEN
  ) {
    worldSocket.send(
      JSON.stringify({
        type: "position",
        position: {
          x: camera.pos[0],
          y: camera.pos[1],
          z: camera.pos[2],
          yaw: camera.rot[1],
          pitch: camera.rot[0],
        },
      }),
    );
  }
}

function syncPlayerPosition(time) {
  if (
    !hasLoadedServerState ||
    time - lastNetworkUpdate < 50 ||
    !worldSocket ||
    worldSocket.readyState !== WebSocket.OPEN
  ) {
    return;
  }

  lastNetworkUpdate = time;
  sendPlayerPosition();
}

function applyServerInventory(serverInventory) {
  if (
    !Array.isArray(serverInventory) ||
    serverInventory.length !== 27
  ) {
    return;
  }

  for (let index = 0; index < inventory.length; index += 1) {
    const item = serverInventory[index];

    if (
      item &&
      typeof item.color === "string" &&
      /^#[0-9a-fA-F]{6}$/.test(item.color) &&
      Number.isInteger(item.count) &&
      item.count > 0 &&
      item.count <= 64
    ) {
      inventory[index] = {
        type: resolveItemType({
          type: item.type,
          color: item.color.toLowerCase(),
        }),
        color: item.color.toLowerCase(),
        count: item.count,
      };
    } else {
      inventory[index] = null;
    }
  }

  renderInventory();
}

function applyServerEdits(edits) {
  if (!Array.isArray(edits)) {
    return;
  }

  blockEdits.clear();

  for (const edit of edits) {
    if (
      !edit ||
      !Number.isInteger(edit.x) ||
      !Number.isInteger(edit.y) ||
      !Number.isInteger(edit.z)
    ) {
      continue;
    }

    const key = blockKey(edit.x, edit.y, edit.z);

    if (edit.color === null) {
      blockEdits.set(key, null);
      continue;
    }

    if (
      typeof edit.color === "string" &&
      /^#[0-9a-fA-F]{6}$/.test(edit.color)
    ) {
      const color = edit.color.toLowerCase();

      blockEdits.set(key, {
        x: edit.x,
        y: edit.y,
        z: edit.z,
        color,
        type: worldBlockTypeFromColor(color),
      });
    }
  }
}

function sendWorldEdit(x, y, z, color) {
  const key = blockKey(x, y, z);
  const edit = {
    x,
    y,
    z,
    color,
  };

  if (
    hasLoadedServerState &&
    worldSocket &&
    worldSocket.readyState === WebSocket.OPEN
  ) {
    worldSocket.send(
      JSON.stringify({
        type: "world_edit",
        x,
        y,
        z,
        color,
      }),
    );
  } else {
    pendingWorldEdits.set(key, edit);
  }
}

function flushPendingWorldEdits() {
  if (
    !hasLoadedServerState ||
    !worldSocket ||
    worldSocket.readyState !== WebSocket.OPEN
  ) {
    return;
  }

  for (const [key, edit] of pendingWorldEdits) {
    blockEdits.set(
      key,
      edit.color === null
        ? null
        : {
            x: edit.x,
            y: edit.y,
            z: edit.z,
            color: edit.color,
            type: itemTypeFromColor(edit.color),
          },
    );

    worldSocket.send(
      JSON.stringify({
        type: "world_edit",
        x: edit.x,
        y: edit.y,
        z: edit.z,
        color: edit.color,
      }),
    );

    pendingWorldEdits.delete(key);
  }
}

function applyWelcome(message) {
  localPlayerId = message.player_id;
  remotePlayers.clear();

  for (const player of message.players || []) {
    if (
      player.id !== localPlayerId &&
      player.position
    ) {
      remotePlayers.set(player.id, player.position);
    }
  }

  const position = message.position;

  if (
    position &&
    Number.isFinite(position.x) &&
    Number.isFinite(position.y) &&
    Number.isFinite(position.z)
  ) {
    camera.pos = [
      position.x,
      position.y,
      position.z,
    ];

    camera.rot = [
      Number.isFinite(position.pitch)
        ? position.pitch
        : 0,
      Number.isFinite(position.yaw)
        ? position.yaw
        : 0,
    ];

    camera.velocityY = 0;
    camera.grounded = false;
  }

  if (!inventoryDirty) {
    applyServerInventory(message.inventory);
  }

  applyServerEdits(message.edits);

  hasLoadedServerState = true;
  lastNetworkUpdate = performance.now();

  for (const [key, edit] of pendingWorldEdits) {
    blockEdits.set(
      key,
      edit.color === null
        ? null
        : {
            x: edit.x,
            y: edit.y,
            z: edit.z,
            color: edit.color,
            type: itemTypeFromColor(edit.color),
          },
    );
  }

  flushPendingWorldEdits();

  if (
    inventoryDirty &&
    worldSocket &&
    worldSocket.readyState === WebSocket.OPEN
  ) {
    worldSocket.send(
      JSON.stringify({
        type: "inventory",
        inventory: inventoryPayload(),
      }),
    );
  }

  sendPlayerPosition();
}

function connectWorldSocket() {
  worldSocket = new WebSocket(socketUrl);

  worldSocket.addEventListener("message", (event) => {
    let message;

    try {
      message = JSON.parse(event.data);
    } catch {
      return;
    }

    if (message.type === "welcome") {
      applyWelcome(message);
      return;
    }

    if (message.type === "inventory_saved") {
      inventoryDirty = false;
      return;
    }

    if (message.type === "player_state") {
      if (
        message.player_id !== localPlayerId &&
        message.position
      ) {
        remotePlayers.set(
          message.player_id,
          message.position,
        );
      }

      return;
    }

    if (message.type === "player_left") {
      remotePlayers.delete(message.player_id);
      return;
    }

    if (
      message.type === "world_edit" &&
      message.edit
    ) {
      const edit = message.edit;

      if (
        !Number.isInteger(edit.x) ||
        !Number.isInteger(edit.y) ||
        !Number.isInteger(edit.z)
      ) {
        return;
      }

      const key = blockKey(edit.x, edit.y, edit.z);

      if (edit.color === null) {
        blockEdits.set(key, null);
        placedBlocks.delete(key);
        return;
      }

      if (
        typeof edit.color === "string" &&
        /^#[0-9a-fA-F]{6}$/.test(edit.color)
      ) {
        const color = edit.color.toLowerCase();

        blockEdits.set(key, {
          x: edit.x,
          y: edit.y,
          z: edit.z,
          color,
          type: worldBlockTypeFromColor(color),
        });
      }
    }
  });

  worldSocket.addEventListener("close", () => {
    hasLoadedServerState = false;
    stopMining();

    window.setTimeout(connectWorldSocket, 2000);
  });

  worldSocket.addEventListener("error", () => {
    worldSocket.close();
  });
}

// =============================================================================
// RAYCASTING
// =============================================================================

function rotate2d([x, y], angle) {
  const sine = Math.sin(angle);
  const cosine = Math.cos(angle);

  return [
    x * cosine - y * sine,
    y * cosine + x * sine,
  ];
}

function raycast(maxDistance = 7) {
  const pitch = camera.rot[0];
  const yaw = camera.rot[1];

  const direction = [
    Math.sin(yaw) * Math.cos(pitch),
    Math.sin(pitch),
    Math.cos(yaw) * Math.cos(pitch),
  ];

  const origin = [
    camera.pos[0],
    camera.pos[1] + EYE_HEIGHT,
    camera.pos[2],
  ];

  const cell = origin.map(Math.floor);

  let previous = null;

  const stepX = Math.sign(direction[0]);
  const stepY = Math.sign(direction[1]);
  const stepZ = Math.sign(direction[2]);

  const deltaX =
    direction[0] === 0
      ? Infinity
      : Math.abs(1 / direction[0]);

  const deltaY =
    direction[1] === 0
      ? Infinity
      : Math.abs(1 / direction[1]);

  const deltaZ =
    direction[2] === 0
      ? Infinity
      : Math.abs(1 / direction[2]);

  let maxX =
    direction[0] > 0
      ? (cell[0] + 1 - origin[0]) / direction[0]
      : direction[0] < 0
        ? (origin[0] - cell[0]) / -direction[0]
        : Infinity;

  let maxY =
    direction[1] > 0
      ? (cell[1] + 1 - origin[1]) / direction[1]
      : direction[1] < 0
        ? (origin[1] - cell[1]) / -direction[1]
        : Infinity;

  let maxZ =
    direction[2] > 0
      ? (cell[2] + 1 - origin[2]) / direction[2]
      : direction[2] < 0
        ? (origin[2] - cell[2]) / -direction[2]
        : Infinity;

  let distance = 0;

  while (distance <= maxDistance) {
    const block = getBlock(cell[0], cell[1], cell[2]);

    if (
      block &&
      (isSolid(cell[0], cell[1], cell[2]) ||
        isDoorBlock(block))
    ) {
      return {
        hit: [...cell],
        previous,
      };
    }

    previous = [...cell];

    const nextDistance = Math.min(maxX, maxY, maxZ);

    if (
      !Number.isFinite(nextDistance) ||
      maxDistance < nextDistance
    ) {
      break;
    }

    if (maxX <= nextDistance + 1e-10) {
      cell[0] += stepX;
      maxX += deltaX;
    }

    if (maxY <= nextDistance + 1e-10) {
      cell[1] += stepY;
      maxY += deltaY;
    }

    if (maxZ <= nextDistance + 1e-10) {
      cell[2] += stepZ;
      maxZ += deltaZ;
    }

    distance = nextDistance;
  }

  return null;
}

// =============================================================================
// MINING AND PLACEMENT
// =============================================================================

function stopMining(source) {
  if (source === undefined) {
    miningSources.clear();
  } else {
    miningSources.delete(source);
  }

  if (miningSources.size === 0) {
    miningTargetKey = null;
    miningStartedAt = 0;

    mineProgressElement.style.display = "none";
    mineProgressElement.style.setProperty(
      "--progress",
      "0deg",
    );
  }
}

function startMining(source) {
  if (inventoryOpen) {
    return;
  }

  const wasEmpty = miningSources.size === 0;

  miningSources.add(source);

  if (wasEmpty) {
    miningTargetKey = null;
    miningStartedAt = 0;
  }
}

function updateMining(time) {
  if (inventoryOpen || miningSources.size === 0) {
    mineProgressElement.style.display = "none";
    return;
  }

  const hit = raycast();

  if (!hit) {
    miningTargetKey = null;
    miningStartedAt = 0;
    mineProgressElement.style.display = "none";
    return;
  }

  const [x, y, z] = hit.hit;
  const targetKey = blockKey(x, y, z);

  if (targetKey !== miningTargetKey) {
    miningTargetKey = targetKey;
    miningStartedAt = time;
  }

  const block = getBlock(x, y, z);
  const heldItem = inventory[selectedSlot];

  if (block && !canHarvest(block, heldItem)) {
    miningStartedAt = time;
    mineProgressElement.style.display = "none";
    setStatus(
      `${requirementText(block)} to mine ${itemDisplayName(block.type)}.`,
    );
    return;
  }

  const progress = Math.min(
    1,
    (time - miningStartedAt) /
      (block
        ? miningDurationMs(block, heldItem)
        : MINE_DURATION_MS),
  );

  mineProgressElement.style.display = "block";
  mineProgressElement.style.setProperty(
    "--progress",
    `${360 * progress}deg`,
  );

  if (progress < 1) {
    return;
  }

  if (breakBlockAt(x, y, z)) {
    miningTargetKey = null;
    miningStartedAt = time;
  } else {
    stopMining();
  }
}

function playerOverlapsCell(x, y, z) {
  return (
    camera.pos[0] + PLAYER_HALF_WIDTH > x &&
    camera.pos[0] - PLAYER_HALF_WIDTH < x + 1 &&
    camera.pos[1] + PLAYER_HEIGHT > y &&
    camera.pos[1] < y + 1 &&
    camera.pos[2] + PLAYER_HALF_WIDTH > z &&
    camera.pos[2] - PLAYER_HALF_WIDTH < z + 1
  );
}

function placeBlock() {
  if (inventoryOpen) {
    return;
  }

  const now = performance.now();

  if (
    now - lastSuccessfulPlacementAt <
    PLACE_COOLDOWN_MS
  ) {
    return;
  }

  const hit = raycast();

  if (hit && isContainerBlock(getBlock(...hit.hit))) {
    lastSuccessfulPlacementAt = now;
    openContainerAt(...hit.hit);
    return;
  }

  const item = inventory[selectedSlot];

  if (!item || item.count <= 0) {
    return;
  }

  if (!hit?.previous) {
    return;
  }

  const [x, y, z] = hit.previous;
  const itemType = resolveItemType(item);

  if (ITEM_DEFINITIONS[itemType]?.placeable === false) {
    setStatus(`${itemDisplayName(itemType)} can't be placed.`);
    return;
  }

  if (itemType === "door") {
    if (!isSolid(x, y - 1, z)) {
      return;
    }

    if (getBlock(x, y, z) || getBlock(x, y + 1, z)) {
      return;
    }

    if (
      playerOverlapsCell(x, y, z) ||
      playerOverlapsCell(x, y + 1, z)
    ) {
      return;
    }

    writeWorldBlock(
      x,
      y,
      z,
      DOOR_BLOCK_COLORS.door_bottom_closed,
      "door_bottom_closed",
    );

    writeWorldBlock(
      x,
      y + 1,
      z,
      DOOR_BLOCK_COLORS.door_top_closed,
      "door_top_closed",
    );
  } else {
    if (
      isSolid(x, y, z) ||
      playerOverlapsCell(x, y, z)
    ) {
      return;
    }

    writeWorldBlock(x, y, z, item.color, itemType);

    if (CONTAINER_KINDS.includes(itemType)) {
      ensureContainer(x, y, z, itemType);
      containersDirty = true;
      saveContainers();
    }
  }

  item.count -= 1;

  if (item.count <= 0) {
    inventory[selectedSlot] = null;
  }

  lastSuccessfulPlacementAt = now;

  renderInventory();
  syncInventory();
}

// =============================================================================
// PLAYER PHYSICS
// =============================================================================

function playerOverlapsBlock(playerX, playerY, playerZ, block) {
  return (
    playerX + PLAYER_HALF_WIDTH > block.x &&
    playerX - PLAYER_HALF_WIDTH < block.x + 1 &&
    playerZ + PLAYER_HALF_WIDTH > block.z &&
    playerZ - PLAYER_HALF_WIDTH < block.z + 1 &&
    playerY + PLAYER_HEIGHT > block.y &&
    playerY < block.y + 1
  );
}

function findOverlappingBlock(x, y, z) {
  const minX = Math.floor(x - PLAYER_HALF_WIDTH);
  const maxX = Math.floor(x + PLAYER_HALF_WIDTH);
  const minZ = Math.floor(z - PLAYER_HALF_WIDTH);
  const maxZ = Math.floor(z + PLAYER_HALF_WIDTH);

  const minY = Math.floor(y + 0.001);
  const maxY = Math.floor(
    y + PLAYER_HEIGHT - 0.001,
  );

  for (let blockX = minX; blockX <= maxX; blockX += 1) {
    for (let blockZ = minZ; blockZ <= maxZ; blockZ += 1) {
      for (let blockY = minY; blockY <= maxY; blockY += 1) {
        const block = getBlock(blockX, blockY, blockZ);

        if (
          block &&
          isSolid(blockX, blockY, blockZ) &&
          playerOverlapsBlock(x, y, z, block)
        ) {
          return block;
        }
      }
    }
  }

  return null;
}

function columnSupportHeight(x, z, startY) {
  const columnX = Math.floor(x);
  const columnZ = Math.floor(z);

  for (
    let y = Math.floor(startY + 1e-9);
    y >= WORLD_MIN_Y;
    y -= 1
  ) {
    if (isSolid(columnX, y, columnZ)) {
      return y + 1;
    }
  }

  return WORLD_MIN_Y;
}

function playerSupportHeight(x, z, startY) {
  const inset = 0.02;

  const samplePoints = [
    [x, z],
    [x - PLAYER_HALF_WIDTH + inset, z - PLAYER_HALF_WIDTH + inset],
    [x + PLAYER_HALF_WIDTH - inset, z - PLAYER_HALF_WIDTH + inset],
    [x - PLAYER_HALF_WIDTH + inset, z + PLAYER_HALF_WIDTH - inset],
    [x + PLAYER_HALF_WIDTH - inset, z + PLAYER_HALF_WIDTH - inset],
  ];

  let supportHeight = WORLD_MIN_Y;

  for (const [sampleX, sampleZ] of samplePoints) {
    supportHeight = Math.max(
      supportHeight,
      columnSupportHeight(sampleX, sampleZ, startY),
    );
  }

  return supportHeight;
}

function tryHorizontalMove(deltaX, deltaZ) {
  const nextX = camera.pos[0] + deltaX;
  const nextZ = camera.pos[2] + deltaZ;
  const supportHeight = playerSupportHeight(
    nextX,
    nextZ,
    camera.pos[1],
  );

  let nextY = camera.pos[1];

  if (camera.grounded) {
    const stepHeight = supportHeight - camera.pos[1];

    if (stepHeight > MAX_STEP_HEIGHT + 1e-9) {
      return;
    }

    if (stepHeight < -0.001) {
      camera.grounded = false;
    } else {
      // Level ground or a step of up to MAX_STEP_HEIGHT: walk onto it.
      nextY = supportHeight;
    }
  }

  if (!findOverlappingBlock(nextX, nextY, nextZ)) {
    camera.pos[0] = nextX;
    camera.pos[1] = nextY;
    camera.pos[2] = nextZ;
  }
}

function updatePhysics(deltaTime) {
  if (inventoryOpen) {
    return;
  }

  let forward = 0;
  let strafe = 0;

  if (keys.KeyW || keys.ArrowUp) {
    forward += 1;
  }

  if (keys.KeyS || keys.ArrowDown) {
    forward -= 1;
  }

  if (keys.KeyD) {
    strafe += 1;
  }

  if (keys.KeyA) {
    strafe -= 1;
  }

  forward += -gamepadMoveY - touchMoveY;
  strafe += gamepadMoveX + touchMoveX;

  const movementLength = Math.hypot(forward, strafe);

  if (movementLength > 0) {
    const normalizedLength = Math.max(1, movementLength);

    forward /= normalizedLength;
    strafe /= normalizedLength;

    const yaw = camera.rot[1];
    const distance = MOVE_SPEED * deltaTime;

    const deltaX =
      (Math.sin(yaw) * forward +
        Math.cos(yaw) * strafe) *
      distance;

    const deltaZ =
      (Math.cos(yaw) * forward -
        Math.sin(yaw) * strafe) *
      distance;

    tryHorizontalMove(deltaX, 0);
    tryHorizontalMove(0, deltaZ);
  }

  if (jumpRequested && camera.grounded) {
    camera.velocityY = JUMP_SPEED;
    camera.grounded = false;
  }

  jumpRequested = false;

  const previousY = camera.pos[1];

  camera.velocityY -= GRAVITY * deltaTime;
  camera.pos[1] += camera.velocityY * deltaTime;
  camera.grounded = false;

  const supportHeight = playerSupportHeight(
    camera.pos[0],
    camera.pos[2],
    camera.pos[1],
  );

  if (
    camera.velocityY <= 0 &&
    camera.pos[1] <= supportHeight
  ) {
    camera.pos[1] = supportHeight;
    camera.velocityY = 0;
    camera.grounded = true;
  }

  const minX = Math.floor(
    camera.pos[0] - PLAYER_HALF_WIDTH,
  );

  const maxX = Math.floor(
    camera.pos[0] + PLAYER_HALF_WIDTH,
  );

  const minZ = Math.floor(
    camera.pos[2] - PLAYER_HALF_WIDTH,
  );

  const maxZ = Math.floor(
    camera.pos[2] + PLAYER_HALF_WIDTH,
  );

  const minY = Math.floor(camera.pos[1] - 1);
  const maxY = Math.floor(
    camera.pos[1] + PLAYER_HEIGHT + 1,
  );

  for (let x = minX; x <= maxX; x += 1) {
    for (let z = minZ; z <= maxZ; z += 1) {
      for (let y = minY; y <= maxY; y += 1) {
        const block = getBlock(x, y, z);

        if (
          !block ||
          !(
            camera.pos[0] + PLAYER_HALF_WIDTH > block.x &&
            camera.pos[0] - PLAYER_HALF_WIDTH < block.x + 1
          ) ||
          !(
            camera.pos[2] + PLAYER_HALF_WIDTH > block.z &&
            camera.pos[2] - PLAYER_HALF_WIDTH < block.z + 1
          )
        ) {
          continue;
        }

        const previousTop = previousY + PLAYER_HEIGHT;
        const currentTop = camera.pos[1] + PLAYER_HEIGHT;

        if (
          camera.velocityY > 0 &&
          previousTop <= block.y + 0.02 &&
          currentTop > block.y
        ) {
          camera.pos[1] = block.y - PLAYER_HEIGHT;
          camera.velocityY = 0;
        }
      }
    }
  }
}

// =============================================================================
// RENDERING
// =============================================================================

const CUBE_VERTICES = [
  [-0.5, -0.5, -0.5],
  [0.5, -0.5, -0.5],
  [0.5, 0.5, -0.5],
  [-0.5, 0.5, -0.5],
  [-0.5, -0.5, 0.5],
  [0.5, -0.5, 0.5],
  [0.5, 0.5, 0.5],
  [-0.5, 0.5, 0.5],
];

const CUBE_FACES = [
  {
    ids: [0, 1, 2, 3],
    neighbor: [0, 0, -1],
    shade: 0.78,
  },
  {
    ids: [4, 5, 6, 7],
    neighbor: [0, 0, 1],
    shade: 1,
  },
  {
    ids: [0, 1, 5, 4],
    neighbor: [0, -1, 0],
    shade: 0.62,
  },
  {
    ids: [2, 3, 7, 6],
    neighbor: [0, 1, 0],
    shade: 1.12,
  },
  {
    ids: [0, 3, 7, 4],
    neighbor: [-1, 0, 0],
    shade: 0.86,
  },
  {
    ids: [1, 2, 6, 5],
    neighbor: [1, 0, 0],
    shade: 0.72,
  },
];

function shadeColor(color, amount) {
  const normalizedColor = color.replace("#", "");

  const red = parseInt(normalizedColor.slice(0, 2), 16);
  const green = parseInt(
    normalizedColor.slice(2, 4),
    16,
  );
  const blue = parseInt(
    normalizedColor.slice(4, 6),
    16,
  );

  const shade = (channel) =>
    Math.max(
      0,
      Math.min(255, Math.round(channel * amount)),
    );

  return `rgb(${shade(red)}, ${shade(green)}, ${shade(blue)})`;
}

function worldToCamera(point) {
  let x = point[0] - camera.pos[0];
  let y = point[1] - (camera.pos[1] + EYE_HEIGHT);
  let z = point[2] - camera.pos[2];

  [x, z] = rotate2d([x, z], camera.rot[1]);
  [y, z] = rotate2d([y, z], camera.rot[0]);

  return [x, y, z];
}

function clipNear(points, near = 0.1) {
  const clipped = [];

  for (let index = 0; index < points.length; index += 1) {
    const current = points[index];
    const previous =
      points[(index + points.length - 1) % points.length];

    const currentInside = current[2] >= near;
    const previousInside = previous[2] >= near;

    if (currentInside !== previousInside) {
      const denominator = current[2] - previous[2];

      if (Math.abs(denominator) > 1e-12) {
        const amount =
          (near - previous[2]) / denominator;

        clipped.push([
          previous[0] +
            (current[0] - previous[0]) * amount,
          previous[1] +
            (current[1] - previous[1]) * amount,
          near,
        ]);
      }
    }

    if (currentInside) {
      clipped.push(current);
    }
  }

  return clipped;
}

function project(point) {
  const scale =
    Math.max(1, 0.55 * Math.min(screenWidth, screenHeight)) /
    point[2];

  return [
    centerX + point[0] * scale,
    centerY - point[1] * scale,
  ];
}

function clipScreenPolygon(points) {
  let polygon = points;

  const boundaries = [
    {
      inside: (point) => point[0] >= 0,
      intersect: (start, end) => {
        const difference = end[0] - start[0];

        if (Math.abs(difference) < 1e-12) {
          return null;
        }

        const amount = -start[0] / difference;

        return [
          0,
          start[1] +
            (end[1] - start[1]) * amount,
        ];
      },
    },
    {
      inside: (point) => point[0] <= screenWidth,
      intersect: (start, end) => {
        const difference = end[0] - start[0];

        if (Math.abs(difference) < 1e-12) {
          return null;
        }

        const amount =
          (screenWidth - start[0]) / difference;

        return [
          screenWidth,
          start[1] +
            (end[1] - start[1]) * amount,
        ];
      },
    },
    {
      inside: (point) => point[1] >= 0,
      intersect: (start, end) => {
        const difference = end[1] - start[1];

        if (Math.abs(difference) < 1e-12) {
          return null;
        }

        const amount = -start[1] / difference;

        return [
          start[0] +
            (end[0] - start[0]) * amount,
          0,
        ];
      },
    },
    {
      inside: (point) => point[1] <= screenHeight,
      intersect: (start, end) => {
        const difference = end[1] - start[1];

        if (Math.abs(difference) < 1e-12) {
          return null;
        }

        const amount =
          (screenHeight - start[1]) / difference;

        return [
          start[0] +
            (end[0] - start[0]) * amount,
          screenHeight,
        ];
      },
    },
  ];

  for (const boundary of boundaries) {
    if (polygon.length === 0) {
      break;
    }

    const previousPolygon = polygon;
    polygon = [];

    for (
      let index = 0;
      index < previousPolygon.length;
      index += 1
    ) {
      const current = previousPolygon[index];
      const previous =
        previousPolygon[
          (index + previousPolygon.length - 1) %
            previousPolygon.length
        ];

      const currentInside = boundary.inside(current);
      const previousInside = boundary.inside(previous);

      if (currentInside !== previousInside) {
        const intersection = boundary.intersect(
          previous,
          current,
        );

        if (
          intersection &&
          Number.isFinite(intersection[0]) &&
          Number.isFinite(intersection[1])
        ) {
          polygon.push(intersection);
        }
      }

      if (currentInside) {
        polygon.push(current);
      }
    }
  }

  return polygon;
}

function faceFacesCamera(
  center,
  normal,
  halfSize = [0.5, 0.5, 0.5],
) {
  const faceCenter = [
    center[0] + normal[0] * halfSize[0],
    center[1] + normal[1] * halfSize[1],
    center[2] + normal[2] * halfSize[2],
  ];

  const cameraDirection = [
    camera.pos[0] - faceCenter[0],
    camera.pos[1] + EYE_HEIGHT - faceCenter[1],
    camera.pos[2] - faceCenter[2],
  ];

  return (
    normal[0] * cameraDirection[0] +
      normal[1] * cameraDirection[1] +
      normal[2] * cameraDirection[2] >
    0
  );
}

function addCubeFaces(faces, block) {
  if (isDoorBlock(block)) {
    addDoorPanelFaces(faces, block);
    return;
  }

  const center = [
    block.x + 0.5,
    block.y + 0.5,
    block.z + 0.5,
  ];

  const cameraVertices = CUBE_VERTICES.map(
    ([x, y, z]) =>
      worldToCamera([
        center[0] + x,
        center[1] + y,
        center[2] + z,
      ]),
  );

  for (const face of CUBE_FACES) {
    const [offsetX, offsetY, offsetZ] =
      face.neighbor;

    if (
      !faceFacesCamera(center, face.neighbor) ||
      isFullCubeBlock(
        block.x + offsetX,
        block.y + offsetY,
        block.z + offsetZ,
      )
    ) {
      continue;
    }

    const points = clipNear(
      face.ids.map((index) => cameraVertices[index]),
    );

    if (points.length < 3) {
      continue;
    }

    const depth =
      points.reduce((total, point) => total + point[2], 0) /
      points.length;

    faces.push({
      depth,
      points,
      color: shadeColor(block.color, face.shade),
    });
  }
}

function addRemoteAvatarFaces(faces, player, color) {
  if (
    !player ||
    !Number.isFinite(player.x) ||
    !Number.isFinite(player.y) ||
    !Number.isFinite(player.z)
  ) {
    return;
  }

  const parts = [
    {
      center: [player.x, player.y + 0.85, player.z],
      scale: [0.65, 0.85, 0.4],
      color,
    },
    {
      center: [player.x, player.y + 1.5, player.z],
      scale: [0.42, 0.42, 0.42],
      color: "#e4bd96",
    },
  ];

  for (const part of parts) {
    const halfSize = part.scale.map(
      (value) => value / 2,
    );

    const cameraVertices = CUBE_VERTICES.map(
      ([x, y, z]) =>
        worldToCamera([
          part.center[0] + x * part.scale[0],
          part.center[1] + y * part.scale[1],
          part.center[2] + z * part.scale[2],
        ]),
    );

    for (const face of CUBE_FACES) {
      if (
        !faceFacesCamera(
          part.center,
          face.neighbor,
          halfSize,
        )
      ) {
        continue;
      }

      const points = clipNear(
        face.ids.map((index) => cameraVertices[index]),
      );

      if (points.length < 3) {
        continue;
      }

      const depth =
        points.reduce((total, point) => total + point[2], 0) /
        points.length;

      faces.push({
        depth,
        points,
        color: shadeColor(part.color, face.shade),
      });
    }
  }
}

function addDoorPanelFaces(faces, block) {
  const isOpen = isOpenDoorBlock(block);

  const panelX = block.x + 0.06;
  const panelZ = block.z + 0.5;

  const panelAxis = isOpen
    ? { x: 0, z: 1 }
    : { x: 1, z: 0 };

  const thicknessAxis = isOpen
    ? { x: -1, z: 0 }
    : { x: 0, z: 1 };

  const bottomY = block.y + 0.01;
  const topY = block.y + 0.99;

  const vertices = CUBE_VERTICES.map(([x, y, z]) => {
    const width = 0.88 * (x + 0.5);
    const thickness = z * 0.08;

    return [
      panelX +
        panelAxis.x * width +
        thicknessAxis.x * thickness,
      y < 0 ? bottomY : topY,
      panelZ +
        panelAxis.z * width +
        thicknessAxis.z * thickness,
    ];
  });

  const cameraVertices = vertices.map(worldToCamera);

  for (const face of CUBE_FACES) {
    let [normalX, normalY, normalZ] =
      face.neighbor;

    const rotatedNormal = [
      panelAxis.x * normalX +
        thicknessAxis.x * normalZ,
      normalY,
      panelAxis.z * normalX +
        thicknessAxis.z * normalZ,
    ];

    const faceVertices = face.ids.map(
      (index) => vertices[index],
    );

    const faceCenter = faceVertices.reduce(
      (center, vertex) => [
        center[0] + vertex[0] / faceVertices.length,
        center[1] + vertex[1] / faceVertices.length,
        center[2] + vertex[2] / faceVertices.length,
      ],
      [0, 0, 0],
    );

    const cameraDirection = [
      camera.pos[0] - faceCenter[0],
      camera.pos[1] + EYE_HEIGHT - faceCenter[1],
      camera.pos[2] - faceCenter[2],
    ];

    if (
      rotatedNormal[0] * cameraDirection[0] +
        rotatedNormal[1] * cameraDirection[1] +
        rotatedNormal[2] * cameraDirection[2] <=
      0
    ) {
      continue;
    }

    const points = clipNear(
      face.ids.map((index) => cameraVertices[index]),
    );

    if (points.length < 3) {
      continue;
    }

    const depth =
      points.reduce((total, point) => total + point[2], 0) /
      points.length;

    faces.push({
      depth,
      points,
      color: shadeColor(block.color, face.shade),
    });
  }
}

function playerColor(playerId) {
  const colors = [
    "#e05252",
    "#4a86df",
    "#55ad68",
    "#d19b39",
    "#a66bd1",
    "#38aaa2",
  ];

  let hash = 0;

  for (const character of playerId) {
    hash = Math.imul(
      hash ^ character.charCodeAt(0),
      16777619,
    );
  }

  return colors[(hash >>> 0) % colors.length];
}

function render() {
  context.fillStyle = "#dce8f2";
  context.fillRect(
    0,
    0,
    screenWidth,
    screenHeight,
  );

  const faces = [];

  const minX =
    Math.floor(camera.pos[0]) - RENDER_RADIUS;
  const maxX =
    Math.floor(camera.pos[0]) + RENDER_RADIUS;

  const minZ =
    Math.floor(camera.pos[2]) - RENDER_RADIUS;
  const maxZ =
    Math.floor(camera.pos[2]) + RENDER_RADIUS;

  for (let x = minX; x <= maxX; x += 1) {
    for (let z = minZ; z <= maxZ; z += 1) {
      const height = terrainHeight(x, z);

      for (
        let y = WORLD_MIN_Y;
        y < height + 7;
        y += 1
      ) {
        const block = getBlock(x, y, z);

        if (block) {
          addCubeFaces(faces, block);
        }
      }
    }
  }

  for (const [key, block] of placedBlocks) {
    if (
      blockEdits.has(key) ||
      block.x < minX - 1 ||
      block.x > maxX ||
      block.z < minZ - 1 ||
      block.z > maxZ ||
      block.y < terrainHeight(block.x, block.z) + 7
    ) {
      continue;
    }

    addCubeFaces(faces, block);
  }

  for (const [key, block] of blockEdits) {
    if (
      !block ||
      placedBlocks.has(key) ||
      block.x < minX - 1 ||
      block.x > maxX ||
      block.z < minZ - 1 ||
      block.z > maxZ ||
      block.y < terrainHeight(block.x, block.z) + 7
    ) {
      continue;
    }

    addCubeFaces(faces, block);
  }

  for (const [playerId, player] of remotePlayers) {
    addRemoteAvatarFaces(
      faces,
      player,
      playerColor(playerId),
    );
  }

  faces.sort((first, second) => {
    return second.depth - first.depth;
  });

  context.save();
  context.beginPath();
  context.rect(0, 0, screenWidth, screenHeight);
  context.clip();

  for (const face of faces) {
    const polygon = clipScreenPolygon(
      face.points.map(project),
    );

    if (polygon.length < 3) {
      continue;
    }

    context.beginPath();
    context.moveTo(polygon[0][0], polygon[0][1]);

    for (let index = 1; index < polygon.length; index += 1) {
      context.lineTo(
        polygon[index][0],
        polygon[index][1],
      );
    }

    context.closePath();
    context.fillStyle = face.color;
    context.fill();

    context.strokeStyle = "rgb(0 0 0 / 12%)";
    context.stroke();
  }

  context.restore();
}

// =============================================================================
// TOUCH CONTROLS
// =============================================================================

function bindVirtualJoystick(
  element,
  onMove,
  onRelease,
) {
  if (!element) {
    return;
  }

  let pointerId = null;

  function updateJoystick(event) {
    const bounds = element.getBoundingClientRect();

    const centerX = bounds.left + bounds.width / 2;
    const centerY = bounds.top + bounds.height / 2;
    const maximumDistance = bounds.width * 0.34;

    let deltaX = event.clientX - centerX;
    let deltaY = event.clientY - centerY;

    const distance = Math.hypot(deltaX, deltaY);

    if (distance > maximumDistance) {
      deltaX = (deltaX / distance) * maximumDistance;
      deltaY = (deltaY / distance) * maximumDistance;
    }

    const knob = element.querySelector(
      ".touch-stick-knob",
    );

    knob.style.setProperty(
      "--knob-x",
      `${deltaX}px`,
    );

    knob.style.setProperty(
      "--knob-y",
      `${deltaY}px`,
    );

    onMove(
      deltaX / maximumDistance,
      deltaY / maximumDistance,
    );
  }

  function releaseJoystick(event) {
    if (event.pointerId !== pointerId) {
      return;
    }

    pointerId = null;

    const knob = element.querySelector(
      ".touch-stick-knob",
    );

    knob.style.setProperty("--knob-x", "0px");
    knob.style.setProperty("--knob-y", "0px");

    onRelease();
  }

  element.addEventListener("pointerdown", (event) => {
    event.preventDefault();

    if (pointerId !== null) {
      return;
    }

    pointerId = event.pointerId;
    element.setPointerCapture(event.pointerId);
    updateJoystick(event);
  });

  element.addEventListener("pointermove", (event) => {
    if (event.pointerId === pointerId) {
      event.preventDefault();
      updateJoystick(event);
    }
  });

  element.addEventListener("pointerup", releaseJoystick);
  element.addEventListener("pointercancel", releaseJoystick);
  element.addEventListener(
    "lostpointercapture",
    releaseJoystick,
  );
}

function bindTouchAction(button, action) {
  let pointerId = null;

  function release(event) {
    if (event.pointerId !== pointerId) {
      return;
    }

    pointerId = null;

    if (action === "mine") {
      stopMining("touch");
    }
  }

  button.addEventListener("pointerdown", (event) => {
    event.preventDefault();

    if (pointerId !== null) {
      return;
    }

    pointerId = event.pointerId;
    button.setPointerCapture(event.pointerId);

    if (action === "jump") {
      jumpRequested = true;
    } else if (action === "mine") {
      startMining("touch");
    } else if (action === "place") {
      placeBlock();
    }
  });

  button.addEventListener("pointerup", release);
  button.addEventListener("pointercancel", release);
  button.addEventListener("lostpointercapture", release);
}

// =============================================================================
// GAMEPAD
// =============================================================================

function readGamepadAxis(gamepad, index, deadZone = 0.16) {
  const value = gamepad.axes[index] || 0;

  return Math.abs(value) < deadZone ? 0 : value;
}

function readGamepadButton(gamepad, index) {
  const button = gamepad.buttons[index];

  return Boolean(
    button && (button.pressed || button.value > 0.55),
  );
}

function risingEdge(action, value) {
  return value && !previousPadActions[action];
}

function moveInventoryCursor(amount) {
  gamepadInventoryCursor =
    (gamepadInventoryCursor + amount + inventory.length) %
    inventory.length;

  if (gamepadInventoryCursor < 9) {
    selectedSlot = gamepadInventoryCursor;
  }

  renderInventory();
}

function activateGamepadInventorySlot() {
  if (gamepadDragSource === null) {
    gamepadDragSource = gamepadInventoryCursor;

    if (gamepadInventoryCursor < 9) {
      selectedSlot = gamepadInventoryCursor;
    }
  } else {
    const sourceIndex = gamepadDragSource;
    const targetIndex = gamepadInventoryCursor;

    if (sourceIndex !== targetIndex) {
      [
        inventory[sourceIndex],
        inventory[targetIndex],
      ] = [
        inventory[targetIndex],
        inventory[sourceIndex],
      ];

      syncInventory();
    }

    gamepadDragSource = null;
  }

  renderInventory();
}

function clearGamepadPressedState() {
  for (const action of Object.keys(previousPadActions)) {
    previousPadActions[action] = false;
  }
}

function updateGamepad() {
  if (!navigator.getGamepads) {
    controllerStatus.textContent =
      " · Controller API unavailable";

    gamepadMoveX = 0;
    gamepadMoveY = 0;
    gamepadLookX = 0;
    gamepadLookY = 0;

    return;
  }

  let gamepad = null;

  try {
    gamepad =
      Array.from(navigator.getGamepads()).find(
        (candidate) => candidate && candidate.connected,
      ) || null;
  } catch {
    gamepad = null;
  }

  if (!gamepad) {
    gamepadMoveX = 0;
    gamepadMoveY = 0;
    gamepadLookX = 0;
    gamepadLookY = 0;

    controllerStatus.textContent =
      " · Controller: not connected";

    clearGamepadPressedState();
    stopMining("gamepad");

    return;
  }

  controllerStatus.textContent =
    ` · Controller: ${gamepad.id || "connected"}`;

  gamepadMoveX = readGamepadAxis(gamepad, 0);
  gamepadMoveY = readGamepadAxis(gamepad, 1);
  gamepadLookX = readGamepadAxis(gamepad, 2);
  gamepadLookY = readGamepadAxis(gamepad, 3);

  const button = (index) =>
    readGamepadButton(gamepad, index);

  const jump = button(0);
  const back = button(1);
  const inventoryButton = button(2);
  const nextSlot = button(3);
  const mine = button(4) || button(6);
  const place = button(5) || button(7);

  const dpadUp = button(12);
  const dpadDown = button(13);
  const dpadLeft = button(14);
  const dpadRight = button(15);

  if (risingEdge("inventory", inventoryButton)) {
    setInventoryOpen(!inventoryOpen);
  }

  if (inventoryOpen) {
    if (risingEdge("dpadUp", dpadUp)) {
      moveInventoryCursor(-9);
    }

    if (risingEdge("dpadDown", dpadDown)) {
      moveInventoryCursor(9);
    }

    if (risingEdge("dpadLeft", dpadLeft)) {
      moveInventoryCursor(-1);
    }

    if (risingEdge("dpadRight", dpadRight)) {
      moveInventoryCursor(1);
    }

    if (risingEdge("jump", jump)) {
      activateGamepadInventorySlot();
    }

    if (risingEdge("back", back)) {
      gamepadDragSource = null;
      setInventoryOpen(false);
    }

    if (openContainerKey) {
      if (risingEdge("place", place)) {
        moveInventoryToContainer(gamepadInventoryCursor);
      }

      if (risingEdge("nextSlot", nextSlot)) {
        takeAllFromContainer();
      }
    }

    stopMining("gamepad");
  } else {
    if (
      risingEdge("dpadLeft", dpadLeft) ||
      risingEdge("dpadUp", dpadUp)
    ) {
      selectedSlot = (selectedSlot + 8) % 9;
      gamepadInventoryCursor = selectedSlot;
      renderInventory();
    }

    if (
      risingEdge("dpadRight", dpadRight) ||
      risingEdge("dpadDown", dpadDown) ||
      risingEdge("nextSlot", nextSlot)
    ) {
      selectedSlot = (selectedSlot + 1) % 9;
      gamepadInventoryCursor = selectedSlot;
      renderInventory();
    }

    if (risingEdge("jump", jump)) {
      jumpRequested = true;
    }

    if (mine) {
      startMining("gamepad");
    } else {
      stopMining("gamepad");
    }

    if (risingEdge("place", place)) {
      placeBlock();
    }
  }

  previousPadActions.jump = jump;
  previousPadActions.mine = mine;
  previousPadActions.place = place;
  previousPadActions.inventory = inventoryButton;
  previousPadActions.back = back;
  previousPadActions.nextSlot = nextSlot;
  previousPadActions.dpadUp = dpadUp;
  previousPadActions.dpadDown = dpadDown;
  previousPadActions.dpadLeft = dpadLeft;
  previousPadActions.dpadRight = dpadRight;
}

// =============================================================================
// EVENT HANDLERS
// =============================================================================

function handleKeyDown(event) {
  if (
    event.code === "KeyE" &&
    !event.repeat
  ) {
    event.preventDefault();
    setInventoryOpen(!inventoryOpen);
    return;
  }

  if (
    event.code === "Escape" &&
    inventoryOpen
  ) {
    gamepadDragSource = null;
    setInventoryOpen(false);
    return;
  }

  if (/^Digit[1-9]$/.test(event.code)) {
    selectedSlot = Number(event.code.slice(5)) - 1;
    gamepadInventoryCursor = selectedSlot;
    renderInventory();
  }

  if (inventoryOpen) {
    return;
  }

  keys[event.code] = true;

  if (
    event.code === "Space" &&
    !event.repeat
  ) {
    toggleTargetedDoor();
    jumpRequested = true;
  }

  if (
    [
      "Space",
      "ArrowUp",
      "ArrowDown",
      "ArrowLeft",
      "ArrowRight",
    ].includes(event.code)
  ) {
    event.preventDefault();
  }
}

function handleKeyUp(event) {
  keys[event.code] = false;
}

function handlePointerDown(event) {
  if (inventoryOpen) {
    return;
  }

  event.preventDefault();

  if (event.button === 2) {
    startMining("mouse");
  } else if (event.button === 0) {
    placeBlock();
  }

  if (document.pointerLockElement !== canvas) {
    canvas.requestPointerLock?.();
  }
}

function handlePointerUp(event) {
  if (event.button === 2) {
    stopMining("mouse");
  }
}

document.addEventListener("keydown", handleKeyDown);
document.addEventListener("keyup", handleKeyUp);

window.addEventListener("blur", () => {
  for (const key of Object.keys(keys)) {
    keys[key] = false;
  }

  jumpRequested = false;
  stopMining();
});

canvas.addEventListener("contextmenu", (event) => {
  event.preventDefault();
});

canvas.addEventListener("pointerdown", handlePointerDown);

window.addEventListener("pointerup", handlePointerUp);

window.addEventListener("pointercancel", () => {
  stopMining("mouse");
});

document.addEventListener("pointerlockchange", () => {
  canvas.style.cursor =
    document.pointerLockElement === canvas
      ? "none"
      : "default";
});

document.addEventListener("mousemove", (event) => {
  if (
    document.pointerLockElement !== canvas ||
    inventoryOpen
  ) {
    return;
  }

  camera.mouseMove(
    event.movementX || 0,
    event.movementY || 0,
  );
});

// =============================================================================
// INITIALIZATION
// =============================================================================

bindVirtualJoystick(
  document.getElementById("moveStick"),
  (x, y) => {
    touchMoveX = x;
    touchMoveY = y;
  },
  () => {
    touchMoveX = 0;
    touchMoveY = 0;
  },
);

bindVirtualJoystick(
  document.getElementById("lookStick"),
  (x, y) => {
    touchLookX = x;
    touchLookY = y;
  },
  () => {
    touchLookX = 0;
    touchLookY = 0;
  },
);

document
  .querySelectorAll("[data-touch-action]")
  .forEach((button) => {
    bindTouchAction(
      button,
      button.dataset.touchAction,
    );
  });

document
  .getElementById("bagButton")
  .addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    setInventoryOpen(!inventoryOpen);
  });

window.addEventListener("gamepadconnected", (event) => {
  controllerStatus.textContent =
    ` · Controller: ${event.gamepad.id || "connected"}`;
});

window.addEventListener("gamepaddisconnected", () => {
  controllerStatus.textContent =
    " · Controller: not connected";

  gamepadMoveX = 0;
  gamepadMoveY = 0;
  gamepadLookX = 0;
  gamepadLookY = 0;

  clearGamepadPressedState();
  stopMining("gamepad");
});

containerCloseButton?.addEventListener("click", closeContainer);

loadContainers();
renderInventory();
updateCoordinates();
connectWorldSocket();

// =============================================================================
// MAIN LOOP
// =============================================================================

let previousTime = performance.now();

function frame(time) {
  const deltaTime = Math.min(
    0.05,
    (time - previousTime) / 1000,
  );

  previousTime = time;

  updateGamepad();

  if (
    !inventoryOpen
  ) {
    camera.mouseMove(
      2.4 * (gamepadLookX + touchLookX) * deltaTime * 200,
      2.4 * (gamepadLookY + touchLookY) * deltaTime * 200,
    );
  }

  updatePhysics(deltaTime);
  updateMining(time);
  updateFurnaces();
  syncPlayerPosition(time);
  updateCoordinates();
  render();

  requestAnimationFrame(frame);
}

requestAnimationFrame(frame);
