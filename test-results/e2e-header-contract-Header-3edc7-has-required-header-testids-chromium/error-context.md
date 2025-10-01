# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - region "Notifications alt+T"
    - generic [ref=e3]:
      - banner [ref=e4]:
        - generic [ref=e6]:
          - generic [ref=e7]:
            - button "Friends of PIFA" [ref=e8] [cursor=pointer]
            - button "← Back to Home" [ref=e9] [cursor=pointer]
          - button "Sign In" [ref=e11] [cursor=pointer]
      - generic [ref=e13]:
        - generic [ref=e14]:
          - heading "Sign In" [level=1] [ref=e15]
          - paragraph [ref=e16]: Enter your email to get a magic link
        - generic [ref=e17]:
          - heading "Welcome back" [level=3] [ref=e19]
          - generic [ref=e20]:
            - generic [ref=e21]:
              - generic [ref=e22]:
                - generic [ref=e23]: Email Address
                - textbox "Email Address" [ref=e24]
              - button "Send Magic Link" [disabled]:
                - generic:
                  - img
                  - generic: Send Magic Link
            - paragraph [ref=e26]: Don't have an account? Contact your league commissioner for an invitation.
        - paragraph [ref=e28]: Having trouble? Contact support for assistance.
  - link "Emergent platform logo Made with Emergent" [ref=e29] [cursor=pointer]:
    - /url: https://app.emergent.sh/?utm_source=emergent-badge
    - generic [ref=e30] [cursor=pointer]:
      - img "Emergent platform logo" [ref=e31] [cursor=pointer]
      - paragraph [ref=e32] [cursor=pointer]: Made with Emergent
```