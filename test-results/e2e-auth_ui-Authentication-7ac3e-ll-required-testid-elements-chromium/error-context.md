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
  - iframe [ref=e24]:
    - generic [ref=f1e2]:
      - generic [ref=f1e3]: "Compiled with problems:"
      - button "Dismiss" [ref=f1e4] [cursor=pointer]: ×
      - generic [ref=f1e5]:
        - generic [ref=f1e6]:
          - generic [ref=f1e7] [cursor=pointer]: ERROR in ./src/components/LoginPage.jsx
          - generic [ref=f1e8]: "Module build failed (from ./node_modules/babel-loader/lib/index.js): SyntaxError: /app/frontend/src/components/LoginPage.jsx: Unterminated JSX contents. (411:10) 409 | </div> 410 | </div> > 411 | </div> | ^ 412 | ); 413 | }; 414 | at constructor (/app/frontend/node_modules/@babel/parser/lib/index.js:359:19) at FlowParserMixin.raise (/app/frontend/node_modules/@babel/parser/lib/index.js:3266:19) at FlowParserMixin.jsxReadToken (/app/frontend/node_modules/@babel/parser/lib/index.js:6502:20) at FlowParserMixin.getTokenFromCode (/app/frontend/node_modules/@babel/parser/lib/index.js:6828:12) at FlowParserMixin.getTokenFromCode (/app/frontend/node_modules/@babel/parser/lib/index.js:5333:13) at FlowParserMixin.nextToken (/app/frontend/node_modules/@babel/parser/lib/index.js:2449:10) at FlowParserMixin.next (/app/frontend/node_modules/@babel/parser/lib/index.js:2362:10) at FlowParserMixin.eat (/app/frontend/node_modules/@babel/parser/lib/index.js:2366:12) at FlowParserMixin.expect (/app/frontend/node_modules/@babel/parser/lib/index.js:3595:15) at FlowParserMixin.jsxParseClosingElementAt (/app/frontend/node_modules/@babel/parser/lib/index.js:6734:10) at FlowParserMixin.jsxParseElementAt (/app/frontend/node_modules/@babel/parser/lib/index.js:6749:37) at FlowParserMixin.jsxParseElementAt (/app/frontend/node_modules/@babel/parser/lib/index.js:6752:32) at FlowParserMixin.jsxParseElement (/app/frontend/node_modules/@babel/parser/lib/index.js:6803:17) at FlowParserMixin.parseExprAtom (/app/frontend/node_modules/@babel/parser/lib/index.js:6813:19) at FlowParserMixin.parseExprSubscripts (/app/frontend/node_modules/@babel/parser/lib/index.js:10619:23) at FlowParserMixin.parseUpdate (/app/frontend/node_modules/@babel/parser/lib/index.js:10604:21) at FlowParserMixin.parseMaybeUnary (/app/frontend/node_modules/@babel/parser/lib/index.js:10584:23) at FlowParserMixin.parseMaybeUnaryOrPrivate (/app/frontend/node_modules/@babel/parser/lib/index.js:10438:61) at FlowParserMixin.parseExprOps (/app/frontend/node_modules/@babel/parser/lib/index.js:10443:23) at FlowParserMixin.parseMaybeConditional (/app/frontend/node_modules/@babel/parser/lib/index.js:10420:23) at FlowParserMixin.parseMaybeAssign (/app/frontend/node_modules/@babel/parser/lib/index.js:10383:21) at /app/frontend/node_modules/@babel/parser/lib/index.js:5634:39 at FlowParserMixin.tryParse (/app/frontend/node_modules/@babel/parser/lib/index.js:3604:20) at FlowParserMixin.parseMaybeAssign (/app/frontend/node_modules/@babel/parser/lib/index.js:5634:18) at /app/frontend/node_modules/@babel/parser/lib/index.js:10353:39 at FlowParserMixin.allowInAnd (/app/frontend/node_modules/@babel/parser/lib/index.js:11955:12) at FlowParserMixin.parseMaybeAssignAllowIn (/app/frontend/node_modules/@babel/parser/lib/index.js:10353:17) at FlowParserMixin.parseParenAndDistinguishExpression (/app/frontend/node_modules/@babel/parser/lib/index.js:11214:28) at FlowParserMixin.parseParenAndDistinguishExpression (/app/frontend/node_modules/@babel/parser/lib/index.js:5727:18) at FlowParserMixin.parseExprAtom (/app/frontend/node_modules/@babel/parser/lib/index.js:10867:23) at FlowParserMixin.parseExprAtom (/app/frontend/node_modules/@babel/parser/lib/index.js:6818:20) at FlowParserMixin.parseExprSubscripts (/app/frontend/node_modules/@babel/parser/lib/index.js:10619:23) at FlowParserMixin.parseUpdate (/app/frontend/node_modules/@babel/parser/lib/index.js:10604:21) at FlowParserMixin.parseMaybeUnary (/app/frontend/node_modules/@babel/parser/lib/index.js:10584:23) at FlowParserMixin.parseMaybeUnaryOrPrivate (/app/frontend/node_modules/@babel/parser/lib/index.js:10438:61) at FlowParserMixin.parseExprOps (/app/frontend/node_modules/@babel/parser/lib/index.js:10443:23) at FlowParserMixin.parseMaybeConditional (/app/frontend/node_modules/@babel/parser/lib/index.js:10420:23) at FlowParserMixin.parseMaybeAssign (/app/frontend/node_modules/@babel/parser/lib/index.js:10383:21) at FlowParserMixin.parseMaybeAssign (/app/frontend/node_modules/@babel/parser/lib/index.js:5685:18) at FlowParserMixin.parseExpressionBase (/app/frontend/node_modules/@babel/parser/lib/index.js:10337:23) at /app/frontend/node_modules/@babel/parser/lib/index.js:10333:39 at FlowParserMixin.allowInAnd (/app/frontend/node_modules/@babel/parser/lib/index.js:11950:16) at FlowParserMixin.parseExpression (/app/frontend/node_modules/@babel/parser/lib/index.js:10333:17) at FlowParserMixin.parseReturnStatement (/app/frontend/node_modules/@babel/parser/lib/index.js:12640:28) at FlowParserMixin.parseStatementContent (/app/frontend/node_modules/@babel/parser/lib/index.js:12292:21) at FlowParserMixin.parseStatementLike (/app/frontend/node_modules/@babel/parser/lib/index.js:12261:17) at FlowParserMixin.parseStatementLike (/app/frontend/node_modules/@babel/parser/lib/index.js:5054:24) at FlowParserMixin.parseStatementListItem (/app/frontend/node_modules/@babel/parser/lib/index.js:12241:17) at FlowParserMixin.parseBlockOrModuleBlockBody (/app/frontend/node_modules/@babel/parser/lib/index.js:12814:61) at FlowParserMixin.parseBlockBody (/app/frontend/node_modules/@babel/parser/lib/index.js:12807:10)"
        - generic [ref=f1e9]:
          - generic [ref=f1e10]: ERROR
          - generic [ref=f1e11]: "[eslint] src/components/LoginPage.jsx Line 411:10: Parsing error: Unterminated JSX contents. (411:10)"
```