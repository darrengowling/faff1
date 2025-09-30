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
              - textbox "Email Address" [ref=e15]: regression-test@example.com
            - generic [ref=e16]:
              - img [ref=e17]
              - generic [ref=e20]: Magic link sent! Check your email or use the link below.
            - button "Send Magic Link" [ref=e21] [cursor=pointer]:
              - generic [ref=e22] [cursor=pointer]:
                - img
                - generic [ref=e23] [cursor=pointer]: Send Magic Link
          - generic [ref=e24]:
            - paragraph [ref=e25]: "Development Mode - Magic Link:"
            - button "Login Now (Dev Mode)" [ref=e26] [cursor=pointer]
            - link "https://test-harmony.preview.emergentagent.com/auth/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InJlZ3Jlc3Npb24tdGVzdEBleGFtcGxlLmNvbSIsImV4cCI6MTc1OTI3NzAwOCwidHlwZSI6Im1hZ2ljX2xpbmsifQ.B5iIW7dDn11lrYfpRSt2l1IAc9QUICRUmmD3MZxTnDI" [ref=e27] [cursor=pointer]:
              - /url: https://test-harmony.preview.emergentagent.com/auth/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InJlZ3Jlc3Npb24tdGVzdEBleGFtcGxlLmNvbSIsImV4cCI6MTc1OTI3NzAwOCwidHlwZSI6Im1hZ2ljX2xpbmsifQ.B5iIW7dDn11lrYfpRSt2l1IAc9QUICRUmmD3MZxTnDI
          - paragraph [ref=e29]: Don't have an account? Contact your league commissioner for an invitation.
      - paragraph [ref=e31]: Having trouble? Contact support for assistance.
  - link "Emergent platform logo Made with Emergent" [ref=e32] [cursor=pointer]:
    - /url: https://app.emergent.sh/?utm_source=emergent-badge
    - generic [ref=e33] [cursor=pointer]:
      - img "Emergent platform logo" [ref=e34] [cursor=pointer]
      - paragraph [ref=e35] [cursor=pointer]: Made with Emergent
```