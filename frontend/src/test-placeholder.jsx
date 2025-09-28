// Temporary test file to verify linter works
export const TestComponent = () => (
  <div>
    <a href="#">This should be caught</a>
    <nav>
      <ul navigationItems={[]}></ul>
    </nav>
  </div>
);