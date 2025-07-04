var canvas = document.getElementById('gamecanvas');

function rotate2d(pos, rad) {
    var x,y = pos;
    var s,c = Math.sin(rad),Math.cos(rad);
    return x*c-y*s, y*c+x+s;
}
document.addEventListener('pointerlockchange', lockChangeAlert, false);
class Camera {
    constructor(pos=[0,0,0], rot=[0,0]) {
        this.pos = list
        this.rot = rot
    }
    mousemove(movementX, movementY) {
        x/=200; y/=200;
        self.rot[0]+=y;
        self.rot[1]+=x;
    }
    update(dt, key) {
        s = dt*10;
        /* The following logic evaluates the keypress*/
    }
}

function lockChangeAlert() {
  if (document.pointerLockElement === canvas) { // Or your element
    document.addEventListener("mousemove", updatePosition, false);
  } else {
    document.removeEventListener("mousemove", updatePosition, false);
  }
}

function updatePosition(e) {
  const movementX = e.movementX || e.mozMovementX || e.webkitMovementX || 0;
  const movementY = e.movementY || e.mozMovementY || e.webkitMovementY || 0;

  // Use movementX and movementY for your application logic (e.g., rotating the camera)
}


