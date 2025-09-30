# Page snapshot

```yaml
- generic [active] [ref=e1]:
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
              - textbox "Email Address" [ref=e15]
            - button "Send Magic Link" [disabled]:
              - generic:
                - img
                - generic: Send Magic Link
          - paragraph [ref=e17]: Don't have an account? Contact your league commissioner for an invitation.
      - paragraph [ref=e19]: Having trouble? Contact support for assistance.
  - link "Emergent platform logo Made with Emergent" [ref=e20] [cursor=pointer]:
    - /url: https://app.emergent.sh/?utm_source=emergent-badge
    - generic [ref=e21] [cursor=pointer]:
      - img "Emergent platform logo" [ref=e22] [cursor=pointer]
      - paragraph [ref=e23] [cursor=pointer]: Made with Emergent
```