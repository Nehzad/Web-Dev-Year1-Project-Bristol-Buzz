(function () {
  if (window.__bristolBuzzRipple) return;
  window.__bristolBuzzRipple = true;

  if (window.matchMedia && window.matchMedia("(any-pointer: coarse)").matches) {
    return;
  }

  var canvas = document.getElementById("water-canvas");
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.id = "water-canvas";
    document.body.insertBefore(canvas, document.body.firstChild);
  }

  var ctx = canvas.getContext("2d");
  var ripples = [];
  var width = 0;
  var height = 0;
  var animationRunning = false;
  var lastRippleAt = 0;

  function resizeCanvas() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
  }

  function Ripple(x, y) {
    this.x = x;
    this.y = y;
    this.radius = 0;
    this.maxRadius = Math.random() * 120 + 70;
    this.lineWidth = 1.5 + Math.random() * 1.5;
    this.color = [
      "rgba(246,200,76,0.42)",
      "rgba(215,232,237,0.32)",
      "rgba(40,96,125,0.38)"
    ][Math.floor(Math.random() * 3)];
  }

  Ripple.prototype.update = function () {
    this.radius += 1.25;
    this.opacity = Math.max(0, 0.55 - this.radius / this.maxRadius);
    return this.radius < this.maxRadius;
  };

  Ripple.prototype.draw = function () {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.strokeStyle = this.color.replace(/0\.\d+\)/, this.opacity.toFixed(3) + ")");
    ctx.lineWidth = this.lineWidth;
    ctx.stroke();
  };

  function addRipple(event) {
    var now = performance.now();
    if (now - lastRippleAt < 70) return;
    lastRippleAt = now;
    var point = event.touches && event.touches.length ? event.touches[0] : event;
    if (!point) return;
    if (ripples.length < 28) {
      ripples.push(new Ripple(point.clientX, point.clientY));
    }
    if (!animationRunning) {
      animationRunning = true;
      requestAnimationFrame(animate);
    }
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);
    for (var i = ripples.length - 1; i >= 0; i--) {
      if (!ripples[i].update()) {
        ripples.splice(i, 1);
      } else {
        ripples[i].draw();
      }
    }
    if (ripples.length) {
      requestAnimationFrame(animate);
    } else {
      animationRunning = false;
    }
  }

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);
  document.addEventListener("mousemove", addRipple);
})();
