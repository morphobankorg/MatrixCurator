🤖 SYSTEM INSTRUCTIONS (DO NOT INCLUDE IN FINAL OUTPUT)
You are an expert software engineer generating a Pull Request description. 
You MUST strictly adhere to the following rules when filling out this template. Failure to comply will break the CI pipeline.

1. SELF-DELETION: You MUST completely DELETE this entire instruction block in your final output.
2. TITLE FORMAT: The PR Title MUST strictly follow the Conventional Commits standard: `<type>[optional scope]: <description>`.
3. CONDITIONAL DELETION (SCREENSHOTS): Evaluate the code diff. IF there are NO visual UI/frontend changes, you MUST completely DELETE the entire "## 📸 Screenshots / Recordings" section, including the table. Do not leave the heading.
4. CONDITIONAL DELETION (BREAKING CHANGES): IF this PR does not introduce breaking changes, you MUST completely DELETE the `<details>` block containing the migration instructions under "## 💥 Breaking Changes".
5. CONDITIONAL DELETION (TICKETS): IF no ticket numbers are provided in your context, you MUST completely DELETE the entire "## 🔗 Related Tickets & References" section.
6. CHECKBOX COMPLIANCE: Under "## 🏷️ Type of Change" and "## ✅ Developer Checklist", DO NOT delete the unchecked items. Mark applicable boxes with `[x]` and leave the rest as `[ ]`.
7. MARKDOWN RULES: All markdown bullet lists MUST strictly use `-` instead of `*`.
8. CLEANUP: You MUST delete all inline helper comments starting with an exclamation mark and the entire Example PR `<details>` block at the bottom.
Output ONLY the final, fully formatted Markdown.

<!--
PR Title MUST follow the Conventional Commits standard:
<type>[optional scope]: <description>
-->

## 📝 Description
<!-- Explain the WHAT and WHY of this change. Provide contextual information. -->

<!-- ⚠️ AI/Human: If there are no UI changes, DELETE the entire Screenshots section below. -->
## 📸 Screenshots / Recordings
| Before | After |
| ------ | ----- |
| <!-- insert image --> | <!-- insert image --> |

## 🧪 How Has This Been Tested?
<!-- Please describe the tests that you ran. -->
- [ ] Added new unit/integration tests
- [ ] Verified existing tests pass
- [ ] Manual testing

> _Steps to reproduce/test:_ 

## 🏷️ Type of Change
<!-- ⚠️ DO NOT delete unchecked items. Just check the applicable boxes. -->
- [ ] **feat:** A new feature (MINOR version bump)
- [ ] **fix:** A bug fix (PATCH version bump)
- [ ] **refactor:** A code change that neither fixes a bug nor adds a feature
- [ ] **perf:** A code change that improves performance
- [ ] **docs:** Documentation only changes
- [ ] **style:** Changes that do not affect the meaning of the code
- [ ] **test:** Adding missing tests or correcting existing tests
- [ ] **chore:** Changes to the build process, CI/CD, or auxiliary tools

## 💥 Breaking Changes
- [ ] **No**
- [ ] **Yes** <!-- If yes, PR title MUST include `!` (e.g., `feat(api)!: drop node 6`). -->

<!-- ⚠️ If there are no breaking changes, DELETE the details block below. -->
<details>
<summary><strong>Migration instructions for Breaking Change</strong></summary>

<!-- Describe how users or other developers should migrate their code/data. -->

</details>

<!-- ⚠️ If there are no related tickets, DELETE the Related Tickets section below. -->
## 🔗 Related Tickets & References
<!-- Example: Closes #123, Refs: #456 -->

## ✅ Developer Checklist
- [ ] My PR title strictly follows `<type>[optional scope]: <description>`.
- [ ] This PR contains a **single responsibility**.
- [ ] I have performed a self-review of my own code.
- [ ] I have added/updated tests to cover my changes.
- [ ] I have updated the documentation accordingly.
- [ ] All markdown lists in this description strictly use `-` instead of `*`.

<br />

<!-- ⚠️ DELETE the entire example block below before opening the PR! -->
<details>
<summary><strong>💡 Click here to see an example of a perfect PR</strong></summary>

### 📝 Example PR

**PR Title:** `feat(search): implement fuzzy matching for user directory API`

**PR Body:**

## 📝 Description
This PR updates the user search endpoint to support fuzzy matching instead of strict exact-string matching. 

**What changed:**
- Enabled the `pg_trgm` extension in PostgreSQL via a new migration.
- Updated the `/api/v1/users` search query to use `ILIKE` and trigram similarity.
- Added a `similarity_threshold` environment variable (defaults to 0.3).

**Why:**
- Support tickets showed users were frustrated when searching for "Jon" did not return "John" or "Jonathan". This dramatically improves the UX of the directory search.

## 🧪 How Has This Been Tested?
- [x] Added new unit/integration tests
- [x] Verified existing tests pass
- [x] Manual testing 

> _Steps to reproduce/test:_ 
> 1. Seed the local database using `npm run db:seed`.
> 2. Hit `GET /api/v1/users?q=micheal` via Postman.
> 3. Verify that the user "Michael" is successfully returned in the payload.

## 🏷️ Type of Change
- [x] **feat:** A new feature (MINOR version bump)
- [ ] **fix:** A bug fix (PATCH version bump)
- [ ] **refactor:** A code change that neither fixes a bug nor adds a feature
- [ ] **perf:** A code change that improves performance
- [ ] **docs:** Documentation only changes
- [ ] **style:** Changes that do not affect the meaning of the code
- [ ] **test:** Adding missing tests or correcting existing tests
- [ ] **chore:** Changes to the build process, CI/CD, or auxiliary tools

## 💥 Breaking Changes
- [x] **No**
- [ ] **Yes** 

## 🔗 Related Tickets & References
Closes #842
Refs: #801

## ✅ Developer Checklist
- [x] My PR title strictly follows `<type>[optional scope]: <description>`.
- [x] This PR contains a **single responsibility**.
- [x] I have performed a self-review of my own code.
- [x] I have added/updated tests to cover my changes.
- [x] I have updated the documentation accordingly.
- [x] All markdown lists in this description strictly use `-` instead of `*`.

</details>
