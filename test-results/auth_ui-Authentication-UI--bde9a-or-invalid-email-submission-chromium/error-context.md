# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e2]:
    - region "Notifications alt+T"
    - generic [ref=e4]:
      - generic [ref=e5]:
        - heading "Sign In" [level=1] [ref=e6]
        - paragraph [ref=e7]: Enter your email to get a magic link
      - generic [ref=e8]:
        - heading "Welcome back" [level=3] [ref=e10]
        - generic [ref=e11]:
          - generic [ref=e12]:
            - generic [ref=e13]:
              - generic [ref=e14]: Email Address
              - textbox "Email Address" [active] [ref=e15]: not-an-email
            - button "Send Magic Link" [ref=e16] [cursor=pointer]:
              - generic [ref=e17] [cursor=pointer]:
                - img
                - generic [ref=e18] [cursor=pointer]: Send Magic Link
          - paragraph [ref=e20]: Don't have an account? Contact your league commissioner for an invitation.
      - paragraph [ref=e22]: Having trouble? Contact support for assistance.
  - link "Emergent platform logo Made with Emergent" [ref=e23] [cursor=pointer]:
    - /url: https://app.emergent.sh/?utm_source=emergent-badge
    - generic [ref=e24] [cursor=pointer]:
      - img "Emergent platform logo" [ref=e25] [cursor=pointer]
      - paragraph [ref=e26] [cursor=pointer]: Made with Emergent
```