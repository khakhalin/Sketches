# Using AI Agents Effectively

This guide will help you work productively with AI coding assistants (like GitHub Copilot Agent) for an existing codebase.

## The Constitution: agents.md

The most important file to keep an eye on is `agents.md` in the repository root. [This file acts as a "constitution" for AI agents](https://agents.md/) unleashed on the project, and it is automatically added to the context of any new chat. It should contain:

- 2-3 lines about what the project is actually doing
- Architecture overview, listing key functionalities, and names of key classes that support these functionalities. You want the agent to be able to `grep` them to quickly orient itself in the code.
- Key concepts, non-trivial assumptions, technical decisions, important information. Libraries that are used bo the project and that need to be kept in mind, but that are not imported in every file.
- Anything critical that is impossible to understand from the code alone (external infrastructure, the size and properties of the data)
- Explanations for all abbreviations and special terms used for variable names, classes, and comments, if they are non-standard or are used idiosyncratically (e.g. if in your project `tmp` consistently means `task management payload`, you need to tell it here)
- Commands (how to run tests, how to run linter formatter etc.)
- Boundaries and rules. Try to formulate these as DOs and not DoNots, as positive language matters for agents! Describe what needs to be true, what needs to always be done; use simple, clear, declarative language. Some examples of what could go there:
  - Prefer pythonic `a.field` to getters `get(a, 'field', None)`; validate with `if hasattr(a, 'field')` if necessary (code style)
  - Don't use defensive checks in the main code to handle incomplete test environments; use mocks and fixtures instead  
  - During development, call `uv run pytest -m fast` often. Once these test work, also run `uv run pytest -m slow`, then `make format`, then make sure `uv run myproject -k 100` outputs current time (rules of development)
  - Don't try to improve the wording of comments and loggers, unless they are no longer true

The `agents.md` file should be concise and efficient as it is attached to _every session_! Ideally make it fit into one page. For the technical overview, you can try to start with a longer text and ask the agent to compress and distill it, although for now agents are not particularly good at distillations, and tend to go too heavy on diagrams. Edit it with your hands. Return to this file often. This is the most important file of your repo! Keep it updated.

After every productive session in which the agent hesitated, or explored the code for longer than usual, or where you had an usual friction that required your intervention, think whether somthint needs to be changed or added to `agents.md`. If you feel that it needs to be updated, try to update it. But also **beware** that this file should be short and dense, every token should matter, precisely because it is added to every session, taking space in the context window. At some point, if there's something critical to add, something less critical may have to go. Treat `agents.md` as meta-code of sorts; review the PRs that change it as critically as you would review a code change!

## Running the session

1. Always start a new chat session for a new PR. If you run the same session for too long, its context gradually erodes, and it can lead the agent astray. It's better to start a new PR with a fresh session and a freshly (automatically) loaded `agents.md`
2. Think of all the files (all code and documentation pieces) that are critical for this PR. Open them in the editor.
3. Make the "main" file (the most important one for this PR) active in the editor. By virtue of being active in VScode, it will be automatically added to the context, to an "honorable" place.
4. Type a good first prompt. Here's an imaginary attempt of writing a "one-shot" prompt:

> We need to add a new transformer to the `UsefulTransformers` class. The context for this change is that we need to support a special case where the field `global_time` is not available. We need to make sure the transformer can handle this, while satisfying API calls from `Separator` classes. Please read files #file:summary.md for general info, then check out the code in files #file:code1.py, #file:code2.py and #file:code3.py. Dig into the raw code of WeirdCustomPackage to check how the base class for `wcp.transformers.transformer` works. Finally, read the test #file:test_code1.py as we'll need to make sure it is still running. The original DoD for this change is copied below. Once you have read everything, come up with 2-3 options for how to design it, and output them in chat (outline pros and cons and indicate your perfonal preference); I will instruct you on which design to implement. If you are missing any information, please ask. _(followed by an empty line, a sequence of --- to mark a start of a quotation, and a simple Ctrl-V or DoD from Jira, or some dump of design notes that you may have)_

As you can see, a good prompt is rather complex. It contains:

1. The motivation for the task (if agents have access to some documentation, or can infer some intentionality from the code and the comments, it may help them to frame the task correctly)
2. A good description of what needs to be done. In the example above this description is rather short (and also completely imaginary), as the example above combines some elements of a design and implementation story. If you know exactly what you want the agent to do, just write it, in as much detail as you can, as if talking to a junior developer.
3. An explicit list of all files that _have_ to be read. You cannot include the whole repo in this list, but try to identify the key texts. If the files are currently open in the VStudio, you don't even need to type `file:` - you just add a hashtag and start typing the name of the file, then pick it from the list. Referencing the file by name without creating an active hashtag-driven link usually also works, but in this case the agent needs to take the initiative and read it, while hashtag-marked files are forced into the context by copilot itself.
4. Name relevant classes and methods literally, exactly as they are called in the code - that way the agent can `grep` them (search for them within the repo) and get extra context if necessary.
5. If you want the agent to dive into some non-standard OSS packages that you use, mention it explicitly, and explain how to best do it (otherwise the agent may try to infer their function from the api only)
6. If you know what to do, and your description is detailed, add "please create a new file named blabla.py" or "please implement the changes" or some other imperative statement to trigger the actual coding action. If, however, you would prefer one more check before letting it loose, ask for it explicitly.
7. Making the agent ask for help (for missing information) is harder than asking it to verify its plans with you; the example the prompt ("If you are missing any info, stop and ask me for help") usually fails, as the agent is optimistic about its knowledge. If you are positive that it _will need_ some extra info from you, word it differently; write: "Before implementing anything, think of 3-5 critical pieces of info that you may be missing, and ask me about them in the chat".
8. After the information-dense main prompt, you may try to add other "additional info" that may or may not be useful (background, log excerpts, error messages etc.). But try not to distract the agent too much; even a slight mistake or obsolete info (e.g. if you paste a mostly-correct but subtly obsolete Jira story) may bias it towards a suboptimal implementation!

Once the agent is coding, you have to sit there and stare at its thinking trace. There are three reasons to keep looking at the trace:

1. If the task runs for too long, copilot will ask you if you're still there, just like Netflix does. Just tell it that yeah you are there.
2. When the agent wants to run a bash command, you'd better see it. If the command is ok, approve it. If it's slightly unproductive, respond to it in the chat instead, correct it, and send the message. If the command is batshit crazy (like, it's trying to install something with `pip`), do the same (answer to it in chat), just with sterner words (ask it to abandon this line of inquiry and recommend what it should do instead).
3. If the thinking trace is clearly bending in a wrong direction, you can also stop the thinking, and type a correction in the box, then send it.

Once the agent is done, and you got the code, go through every line. Read every line! Check for these common mistakes that AI is still prone to:

1. Make sure it didn't re-implement something that is already available, either as a standard functionality in a standard tool, or as an existing helper method in the repo. As agent has no memory from the repo, it is at mercy of our `agents.md`, documentation, and limited code exploration, in terms of learning what is already available.
2. Conversely, don't let it install and import new packages unless you believe it's needed. Newer models do it less often, but sometimes they still try to help a bit too radically.
3. Make sure it didn't try to improve the code you didn't ask it to improve - these "passing by" casual improvements are always more risky than the main task
4. Don't let it remove or radically rewrite older comments left in the code. Sometimes it gets carried away.
5. Agents have a tendency to overemphasize their recent experiences: e.g. if they made a mistake, and you correct it in the chat, they may try to mention this mistake and its correction very specifically in the comments within the code, or in the documents. For you it's just a tiny thing that happened in the latest 5 min of your multi-decade life, but for them it's 30% of their entire window content. Don't let the agent overshare these minutiae, it is not helpful.

# Advanced Topics

## Beyond a one-shot prompt: Design and Scoping

AI-assisted coding works best with focused, concrete, scope-limited tasks. If what you are trying to do is more ambitious, try to break your task apart into several subtasks. For example, when developing a feature, ask the agent to develop a good unit test _first_. Explain the feature, provide a description, let it write a test (warning it it that the test cannot be run yet, as the feature does not exist yet). Check the test, and make sure you like it. Then give it the second task - writing the feature to satisfy the test.

An even better approach, which is especially important for larger, more ambitious tasks, is to disentangle planning and implementation tasks. You may for example try to follow this scenario:

1. First describe the problem to the agent. Then go through the following prompts:
2. Given the task, examine the code already in the repo. Summarize the current state of it, the key classes, use patterns, design elements, their interactions with the rest of the repo. Identify weak and strong aspects of the current design. Check how the current code is tested and summarize this as well.
3. Given the task and the current code, design the architecture of this new feature / refactoring. Come up with several design proposals, for each of them outline their pros and cons, and indicate which of one of these you personally recommend.
4. Given the current code and the description of the target design, come up with a list of small atomic steps that would bring us from the current state to the target state. Describe the changes to the tests that are needed, and place these changes proactively, to follow state-based development. At the end of the document, list the acceptance criteria (DoD: the Definition of Done)

Once you have the list of steps, you can ask them to implement steps 1-4, steps 5-6 etc., reviewing the code at every step, if necessary.

For this step-wise approach to work, you want to migrate from working with the chat only to working with markdown documents! At each step, create a new `.md` document and ask the agent to output the result to this md (by hashtag-referencing it). Once the output is ready, review it, and edit it as needed! Make sure you like it, before going to the next step! If the assessment of the code, the design, or the DoD need correction - correct it. Then, once it's time to proceed, you can either reference this `.md`, or copy it in the chat. For example, in case of design proposals, it's better to copy the proposal that you liked in the chat, and not include other proposals, as it may erode the context and confuse the agent. If doing so, don't forget to close or unfocus the `.md`, to prevent it from getting added to the context "by mistake".

For now, there's no "best practice" for how to organize these md files, and for whether they need to be saved "for posterity". Most probably, in the next few months it will become normative to save them, as a part of repo history / documentation, as prompts are generally too verbose to include in either commit messages or PR descriptions, but they may be important for understanding the changes in the code later on. But for now there is no standard for how to do it.

Crucially, _start a new session_ for each new step, then reference the files you need. You want the context window to be as free as possible for the agent to do its best work. Sometimes you can combine "explore" and "design" phases, but if you ever hit the point of [context compaction](https://deepwiki.com/openai/codex/3.7-context-compaction), game over, just start a new session. (In Copilot you would see the agent pausing with a message "Summarizing conversation history...") Nothing is dead at this point, you could still continue, but you would notice that the agent would start making factual mistakes about the contents of some files, while assuming that it remembers the contents of these files. If you have your `md` outputs, it's better to just start anew.

## Adversarial process

Recently a new approach to developing with agent was proposed, that is sometimes referred to as **Iterative Adversarial Refinement** [ref1](https://gist.github.com/dollspace-gay/45c95ebfb5a3a3bae84d8bebd662cc25), [ref2](https://github.com/oaustegard/claude-skills/releases?q=crafting-instructions&expanded=true). In this process, you start with following through the steps described above, but then, once everything is implemented, you add an extra step:

* Do a git diff between this branch and `main` branch. Pretend you're a senior dev doing a code review and you HATE this implementation. Does it even work? Are the requirements satisfied? Are the tests good? Are there any missed edge cases, vulnerabilities, code smells? Is it performant? Is it well designed? Will it be easy to maintain in the long-term? Be tough but fair; if something is good, acknowledge it, but concentrate on weak points. For weaknesses, be reserved and practical: explain why it is bad, then outline the direction of the change, fix, or alternative. Lead with the hardest critiques. Output your analysis to NEWFILE.md

Once you receive the critique, analyze it. Classify all identified weaknesses into four groups:

1. Critiques that are not true because the agent doesn't know something that you know (external limitations, future plans etc.)
2. Critiques with which you disagreee because they are silly, outright hallucinated, or that disagree with your personal taste
3. When 2-3 competing designs are possible, and after you decided to try design A, an attempt to move to an alternative B or C, just because it is different (also possible, and about equally bad, but different)
4. Legitimate critique with which you agree

Pick 1-2 legitimate critiques, and ask the agent to implement them. **Then repeat this step!** Keep repeating this until you no longer have anything in category (4): that is, until all critiques are fake or untrue.

Critically, to follow this approach you need to start a new session every time, and carefully curate the information flow. The critic should always criticize the code _as is_: it should have access _only_ to the code (the output of `git diff` tool) and the description of the feature (either your original prompt, or the "acceptance criteria" / DoD that you formulated). Nothing else. It should not see the reasoning of the "designer" agent, it should not know any pros and cons that you considered, it should start from scratch, or it will get derailed into just reiterating and expanding on the aspects you already considered. To have a fresh look, you need to ask a fresh agent.

## Documentation for humans

When using agents for _writing documentation_, be triple-careful, as we don't have unit tests for documentation, so we don't have any way to tell if the generated text is "true" in any sense of this word, and even less so, if it is good, or helpful. At the same time, vague, wordy, obsolete, or hallucinated documentation is a form of technical debt, and an expensive one at that. LLM agents have a reverence for `.md` documents: they tend to believe them more than the code itself, so any lie or obsolete info in the documents may erode the performance of an agent. Yet unless you ask about it very specifically, it won't complain; it will just produce suboptimal code.

So please be very careful and very deliberate when using agents for writing or editing the docs. The value of a good doc is that it gives you the info you need, but not more. LLMs are not good at achieving this balance. They are bad at generalization, at not going on a tangent. So please, don't let them pollute the docs! Docs are our treasure.

Agents are also horrible in terms of the style. They can masterfully imitate three styles: Linkedin slop, boring bureaucratic language, and overcasual writing of social media grifters. Neither works for documentation. The only way to get reasonable docs from an agent is to find some docs that you personally like, open them, and explicitly point to this md in your prompt with something like "Please read #file:good_file.md and #file:another.md as a style reference. Try to imitate their language and approach to documentation in your writing". And even then you have to manually edit the result, pruning and deleting a lot, and rewriting whole sentences.

Quite notably, giving an agent a good example of writing, asking it to transform it into a prompt, and adding this prompt to `agents.md` doesn't work. Agents can't introspect, and they can't one-shot guess what stylistic prompt would cause what input, at the point that they are fed this prompt. Perhaps it's possible to find a good prompt by iteration, but at present it seems to be easier to just point them at a good example document, and ask it to follow its style.

## Documentation for agents

With agentic development, we are writing not only for humans, but also for agents! Documentation is the only way for agents to learn the overall goals of the project, the lore, the mission, and the externalities (customers, data sources, the business side of things: basically everything that is not directly visible in the repo). So what is the SOTA for writing documentation for agents?

The problem is that as of early 2026 [there's no SOTA](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents). No one knows how to do it best! And as models keep changing, it's quite possible that the "best solution" will change in the next few months! Here's a short list of things we _do not know_:

1. How large should be the overview that goes in the "agent constitution" (agents.md or github instructions)? How to best create it? Is there a way to distill it programmatically?
2. Should we write the same set of docs for humans and for agents, or should we write different stuff for different audiences?
3. Is there a hope that agents would maintain their own documentation for themselves ([Letta](https://www.letta.com/) or [Zettelkasten](https://en.wikipedia.org/wiki/Zettelkasten)-style), or is it better (at least in large, mature projects) to have the knowledge base maintained by humans?
4. Is it better to have larger docs, and shorter docstrings, or is it better to keep most info in docstrings? There's obviously no need in maintaining both. So which one to prioritize?
5. How to best refer to the code from the docs? Links to `.py` files? Mentions of file names? Mentions of key objects (for the agent to `grep` them)? Code snippets roughly matching the code?
6. Is it possible to do progressive disclosure with mds? (Offer an md with links to other mds, each link promising what is there; then in the 2nd order file offer some important info, but also more links with references, etc.) Can agents leverage progressive disclosure with md-based documentation, or does one need RAGs / Tools to maintain it?
7. Is it worth it to create a separate [Skill](https://code.claude.com/docs/en/skills) to work with the project, properly referencing the documenation, bash commands etc? Or will Anthropic / OpenAI etc. invest in "out of the box" support for existing documentation in their next models?

None of that is known yet. There's lots of room for experimentation!

## Teaching the Agent Over Time

Within a single conversation session, the agent remembers what you teach it. We may sometimes try to use this. If you feel that the session was particularly productive, or had a strong friction where the agent had to perform a lot of research, or you had to correct it a lot, you may try to use this prompt:

> Let's take a step back and re-group. Re-read your #file:agents.md and think whether you learned or experienced anything new in this session, either from reading the code, or from interacting with me, that warrants an update of your constitution in agents.md? If so, propose your changes.

Compare agent's ideas to the text of `agents.md`. These ideas are almost always too verbose and generous in terms of adding text to this compact document. Agents _can't introspect_ their own state, so as a rule, they cannot generate good prompts for themselves. Still, look at the proposal and think if maybe something may indeed be updated or improved here.
