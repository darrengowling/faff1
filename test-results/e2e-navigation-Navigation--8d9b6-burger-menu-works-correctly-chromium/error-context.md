# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e2]:
    - region "Notifications alt+T"
    - generic [ref=e3]:
      - banner [ref=e4]:
        - generic [ref=e6]:
          - generic [ref=e7]:
            - button "Friends of PIFA" [ref=e8] [cursor=pointer]
            - button "← Back to Home" [ref=e9] [cursor=pointer]
          - generic [ref=e10]:
            - button "Sign In" [ref=e11] [cursor=pointer]
            - button "☰" [active] [ref=e12] [cursor=pointer]
      - generic [ref=e14]:
        - generic [ref=e15]:
          - heading "Sign In" [level=1] [ref=e16]
          - paragraph [ref=e17]: Enter your email to get a magic link
        - generic [ref=e18]:
          - heading "Welcome back" [level=3] [ref=e20]
          - generic [ref=e21]:
            - generic [ref=e22]:
              - generic [ref=e23]:
                - generic [ref=e24]: Email Address
                - textbox "Email Address" [ref=e25]
              - button "Send Magic Link" [disabled]:
                - generic:
                  - img
                  - generic: Send Magic Link
            - paragraph [ref=e27]: Don't have an account? Contact your league commissioner for an invitation.
        - paragraph [ref=e29]: Having trouble? Contact support for assistance.
  - link "Emergent platform logo Made with Emergent" [ref=e30] [cursor=pointer]:
    - /url: https://app.emergent.sh/?utm_source=emergent-badge
    - generic [ref=e31] [cursor=pointer]:
      - img "Emergent platform logo" [ref=e32] [cursor=pointer]
      - paragraph [ref=e33] [cursor=pointer]: Made with Emergent
```