# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - region "Notifications alt+T"
    - banner [ref=e4]:
      - generic [ref=e6]:
        - button "Friends of PIFA" [ref=e7] [cursor=pointer]:
          - img [ref=e9] [cursor=pointer]
          - generic [ref=e15] [cursor=pointer]: Friends of PIFA
        - navigation
        - generic [ref=e16]:
          - button "New League" [ref=e17] [cursor=pointer]:
            - img
            - text: New League
          - generic [ref=e18]:
            - generic [ref=e19]: Welcome, commish@example.com
            - button "Dashboard" [ref=e20] [cursor=pointer]
          - button "Switch to dark mode" [ref=e21] [cursor=pointer]:
            - generic [ref=e22] [cursor=pointer]:
              - img
      - link "Skip to main content" [ref=e23] [cursor=pointer]:
        - /url: "#main-content"
    - main [ref=e24]:
      - generic [ref=e27]:
        - img [ref=e29]
        - heading "Email Not Verified" [level=3] [ref=e32]
        - paragraph [ref=e33]: Please verify your email address to continue.
  - link "Emergent platform logo Made with Emergent" [ref=e34] [cursor=pointer]:
    - /url: https://app.emergent.sh/?utm_source=emergent-badge
    - generic [ref=e35] [cursor=pointer]:
      - img "Emergent platform logo" [ref=e36] [cursor=pointer]
      - paragraph [ref=e37] [cursor=pointer]: Made with Emergent
```