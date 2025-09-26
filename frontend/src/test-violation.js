// This file should trigger SSR safety violations
const x = window.location;
const y = document.getElementById('test');
const z = navigator.userAgent;

console.log(x, y, z);