# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - region "Notifications alt+T"
    - generic [ref=e3]:
      - banner [ref=e4]:
        - generic [ref=e6]:
          - button "Friends of PIFA" [ref=e8] [cursor=pointer]
          - button "Sign In" [ref=e10] [cursor=pointer]
      - generic [ref=e12]:
        - generic [ref=e13]:
          - heading "Sign In" [level=1] [ref=e14]
          - paragraph [ref=e15]: Enter your email to get a magic link
        - generic [ref=e16]:
          - heading "Sign In" [level=3] [ref=e18]
          - generic [ref=e19]:
            - generic [ref=e20]:
              - generic [ref=e21]:
                - generic [ref=e22]: Email Address
                - textbox "Email Address" [disabled] [ref=e23]: playwright-test@example.com
              - button "Sending Magic Link" [disabled]:
                - generic:
                  - generic: Sending Magic Link
            - paragraph [ref=e25]: Don't have an account? Contact your league commissioner for an invitation.
        - paragraph [ref=e27]: Having trouble? Contact support for assistance.
  - link "Emergent platform logo Made with Emergent" [ref=e28] [cursor=pointer]:
    - /url: https://app.emergent.sh/?utm_source=emergent-badge
    - generic [ref=e29] [cursor=pointer]:
      - img "Emergent platform logo" [ref=e30] [cursor=pointer]
      - paragraph [ref=e31] [cursor=pointer]: Made with Emergent
```