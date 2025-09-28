// Test file to check if ESLint rule catches browser global usage at module scope
const currentUrl = window.location.href;
const userAgent = navigator.userAgent;
document.title = "Test";
const standalone = window;

// This should be allowed (inside function)
function testFunction() {
  const url = window.location.href;
  return url;
}

// This should also be allowed (typeof check)
const hasWindow = typeof window !== 'undefined';