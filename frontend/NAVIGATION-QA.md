# Frontend navigation and interaction pass

## Changes

- Pricing is reachable from every public navigation bar. Mobile navigation closes on route changes and Escape, restoring focus to the toggle.
- Homepage workspace preview headings link to Projects, Overview, and GEO.
- Plan cards carry the selected plan and billing cadence to signup. Signup displays the selected plan as an interest, not a purchased subscription.
- Footer email entry prefills signup; the copy explicitly states that it does not subscribe the visitor.
- Project avatars open account settings. Noninteractive date labels no longer pretend to be dropdowns.
- The primary frontend sorts live project cards by name. The single-project generic edition shows a count instead of an ineffective sort menu.
- Content-default selections can be saved and restored in session storage. Editing a field clears the saved indicator. These preferences do not configure server-side generation.
- Ranking bars respond to clicks as well as focus and hover.
- Ctrl/Cmd+K focuses the projects/dashboard search field. Dashboard search resets between pages.
- Loading, retry, and not-found states provide usable recovery paths.
- Section entrance motion, image/card hover effects, dialog transitions, and button press feedback respect reduced-motion preferences.
- Responsive fixes include compact mobile CTA buttons, wrapped toolbars, readable form text, constrained dialogs, and footer wrapping.

## Verification

Primary frontend browser checks covered Home, Pricing, Sign in, Sign up, Projects, Overview, SEO, GEO, History, Settings, Notifications, and Library at 390, 768, and 1440 px. No document-level horizontal overflow was observed.

Checked mobile menu opening, pricing-to-signup plan context, and saving/restoring content defaults across tabs. TypeScript and production builds are checked separately for both editions.

The source audit checks literal internal routes and flags buttons/selects without handlers. It is not proof that every backend integration works. Authentication, publishing, billing, and other live actions still require their configured services. No real account, subscription, or publication was created during QA.
