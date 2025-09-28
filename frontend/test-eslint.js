// Test file to check if ESLint rule catches browser global usage at module scope
const currentUrl = window.location.href;
const userAgent = navigator.userAgent;
document.title = "Test";