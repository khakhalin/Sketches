# Using AI Agents Effectively

This is my take on agentic coding with VS Code and GitHub Copilot, as of January 2026, assuming that you work with an existing codebase, on a tightly planned research project, and so would like to retain a high level of control over the code. That is to say, the process I'm describing here does not feel like pure vibe-coding. It's just a type of coding where you communicate largely with "normal English", and couch almost no code directly, but where you still try to obsessively retain decision power over what is happening to your codebase.

## The Constitution: agents.md

Before we talk about actual prompts and processes, let's discuss the most important file to keep an eye on: the [`agents.md`](https://agents.md/) in the repository root. This file acts as a "constitution" for Copilot agents unleashed on the project, and it is automatically added to the context of any new chat. You can think of it as the "minimal awareness document" that a newborn agent will possess: this file and your prompt will be _the only memory_ that our amnesiac helpers will retain about your codebase, from one session to another. Which is why we want to get it right.

For an existing repo, the `agents.md` file should contain:

- 2-3 lines that tell what this project is actually doing (the motivation, the human context)
- Architecture overview, listing key functionalities, and the names of key classes supporting these functionalities. In general, there are two ways to orient the agent within the project:
  - We can reference an existing file using `@filename` (if the file is unique) or `/dir/dir/filename` (starting from the repo root) if it's not.
  - We can name the class or the method, hoping that the agent would `grep` it (nore on it below)
- List some key concepts, critical information, non-trivial assumptions, technical decisions, names of libraries that are used in the project but are not imported in every file. Everything that could help.
- Any critical info that is impossible to understand from the code alone: the size and properties of your data, your tech stack and external infrastructure (just list 4-5 keywords), etc.
- Explanations for all the abbreviations and special terms that are used in the project, either as parts of variable names, classes, or comments, _especially_ if they are non-standard or are used idiosyncratically. For example, if within your project `tmp` consistently means `task management payload`, you'd better write it here! Otherwise the agent will try to guess the names of variables, and will do it incorrectly.
- Commands and tools: how to run tests, how to run the linter/formatter, etc.
- Boundaries and rules. Try to formulate these as DOs rather than DoNots, as agents are more likely to follow positive language. Give them a pep talk! Describe what needs to be true, what needs to always be done; use simple, clear, declarative language.
- If your project depends on some packages that may not be familiar to the agent, either because they are younger than the training cut-off date, or because they are yours and private, name them here. Warn the agent that your project heavily depends on a package MyProjectOne that is installed locally. "Never assume its behavior from API/naming; read the raw code several dependencies deep!"
- This section will also contain 2-3 specific statements that will encourage the agent to explore before performing the tasks, and will give it the tools to do so. Let me just write you the exact text that I use, and we can talk about it later:

My typical rules from a typical `agents.md`:

```Markdown
# Rules (Mandatory)
1. Never assume you have complete information. Start by seeking information you lack!
2. Get background info: Find matching topics in the list below, `read` referenced files, and `grep` key tokens to learn more
3. For design tasks, always check @docs/index.md and @overview.md
4. After reading, generate a plan of actions. For large tasks, offer 2-5 options, provide pros and cons, indicate your preference. Pause and ask for input.
5. Prefer pythonic `a.field` to getters like `get(a, 'field', None)`; validate with `if hasattr(a, 'field')` if necessary
6. Don't use defensive checks in the main code to handle incomplete test environments; use mocks and fixtures instead
7. During development, call `uv run pytest -m fast` often. Once these tests work, run `uv run pytest -m slow`, then `make format`, then make sure `uv run myproject -k 10` converges
8. Preserve the wording of existing comments and loggers, unless they are no longer true.
```

The most interesting part of this prompt is the second point: the invitation for the agent to seek information proactively. For it to work, you follow the `Rules` section with the following section:

```Markdown
# Lookup by Topic

## Schemas, Data Engineering
read: @data_engineering.md
grep: ingester, schema_validator

## Performance, Spark
read: spark.md
grep: break_dag, repartition
```

...and so on. Basically, you give your agent a dictionary that maps PR topics, human concepts, and local jargon of the team to key elements of the repo. By doing so, we model _Progressive Disclosure_, giving the agent a way to request information as it is needed, instead of forcing it to read the entire documentation at once. Both the keywords and the greppable terms should loosely follow the TF-IDF logic: we want sticky texts that work (that would grasp the agent's attention), and entry points that are efficient. If we hit this balance, the agent will always react as if it is familiar with the repo, which is frankly a bizarre, almost unsettling experience!

As the `agents.md` file is attached to _every session_, it should be concise and efficient. We want it to be under 4000 characters or so, and it is OK to strip it of most formating, except of those that you use for emphasis (like making `# Mandatory` above an h1 title, for example). Everything else should be optimized for space. There's no reason to save on articles, as these are single tokens anyways, but you can compromise on grammar. For the technical overview part, it helps to start with a longer text, then ask the agent to compress and distill it, then rewrite it from scratch manually, as for now agents typically do a very bad job in distilation. Edit the overview manually.

But at the same time, return to this file often. This is the most important file in your repo! Keep it updated. After every productive session in which the agent hesitated, or explored the code for longer than usual, or where you had unusual friction that required your intervention, think about whether something can be changed in the `agents.md`. Treat `agents.md` as meta-code of sorts; review the PRs that change it as critically as you would review a requested change to the code.

## Running the session

1. Always start a new chat session for a new PR. If you run the same session for too long, its context gradually erodes, and it can lead the agent astray. It's better to start a new PR with a fresh session and a freshly (automatically) loaded `agents.md`.
2. Think of all the files (all code and documentation pieces) that are critical for this PR. Open them in the editor.
3. Make the "main" file (the most important one for this PR) active in the editor. By virtue of being active in VS Code, it will be automatically added to the context in an "honorable" place.
4. Type a good first prompt. Here's an imaginary attempt at writing a "one-shot" prompt:

```
We need to add a new transformer to the `UsefulTransformers` class. The context for this change is that we need to support a special case where the field `global_time` is not available. We need to make sure the transformer can handle this, while satisfying API calls from `Separator` classes. Please read the file #file:summary.md for general info, then check out the code in files #file:code1.py, #file:code2.py, and #file:code3.py. Dig into the raw code of WeirdCustomPackage to check how the base class for `wcp.transformers.transformer` works. Finally, read the test #file:test_code1.py as we'll need to make sure it is still running. The original DoD for this change is copied below. Once you have read everything, come up with 2-3 options for how to design it, and output them in chat (outline pros and cons and indicate your personal preference); I will instruct you on which design to implement. If you are missing any information, please ask. _(followed by an empty line, a sequence of --- to mark the start of a quotation, and a simple Ctrl-V or DoD from Jira, or some dump of design notes that you may have)_
```

As you can see, a good prompt is rather complex. It contains:

1. The motivation for the task (if agents have access to some documentation, or can infer some intentionality from the code and the comments, it may help them frame the task correctly)
2. A good description of what needs to be done. In the example above, this description is rather short (and also completely imaginary), as the example above combines some elements of a design and implementation story. If you know exactly what you want the agent to do, just write it, in as much detail as you can, as if talking to a junior developer.
3. An explicit list of all files that _have_ to be read. You cannot include the whole repo in this list, but try to identify the key texts. If the files are currently open in VS Code, you don't even need to type `file:` - you just add a hashtag and start typing the name of the file, then pick it from the list. Referencing the file by name without creating an active hashtag-driven link usually also works, but in this case the agent needs to take the initiative and read it, while hashtag-marked files are forced into the context by Copilot itself.
4. Name relevant classes and methods literally, exactly as they are called in the code - that way the agent can `grep` them (search for them within the repo) and get extra context if necessary.
5. If you want the agent to dive into some non-standard OSS packages that you use, mention it explicitly, and explain how to best do it (otherwise the agent may try to infer their function from the API only)
6. If you know what to do, and your description is detailed, add "please create a new file named blabla.py" or "please implement the changes" or some other imperative statement to trigger the actual coding action. If, however, you would prefer one more check before letting it loose, ask for it explicitly.
7. Making the agent ask for help (for missing information) is harder than asking it to verify its plans with you; the example the prompt ("If you are missing any info, stop and ask me for help") usually fails, as the agent is optimistic about its knowledge. If you are positive that it _will need_ some extra info from you, word it differently; write: "Before implementing anything, think of 3-5 critical pieces of info that you may be missing, and ask me about them in the chat".
8. After the information-dense main prompt, you may try to add other "additional info" that may or may not be useful (background, log excerpts, error messages etc.). But try not to distract the agent too much; even a slight mistake or obsolete info (e.g. if you paste a mostly-correct but subtly obsolete Jira story) may bias it towards a suboptimal implementation!

Once the agent is coding, you have to sit there and stare at its thinking trace. There are three reasons to keep looking at the trace:

1. If the task runs for too long, Copilot will ask you if you're still there, just like Netflix does. Just tell it that yes, you are there.
2. When the agent wants to run a bash command, you'd better see it. If the command is OK, approve it. If it's slightly unproductive, respond to it in the chat instead, correct it, and send the message. If the command is violently wrong (like it's trying to install something with `pip`), do the same (answer to it in chat), just with sterner words (ask it to abandon this line of inquiry and recommend what it should do instead).
3. If the thinking trace is clearly bending in a wrong direction, you can also stop the thinking and type a correction in the box, then send it.

Once the agent is done, and you got the code, go through every line. Read every line! Check for these common mistakes that AI is still prone to:

1. Make sure it didn't re-implement something that is already available, either as a standard functionality in a standard tool, or as an existing helper method in the repo. As the agent is not a whale, and it cannot ingest the entire repo in one go, it is at the mercy of our `agents.md`, documentation, and limited code exploration that it will perform based on your prompt and the context. If some functionality is there, but is hidden just a little too well, it may not ever discover it.
2. Conversely, don't let it install and import new packages unless you believe it's needed. Newer models do it less often, but sometimes they still try to help a bit too radically (especially when frustrated with how the coding goes).
3. Make sure it didn't try to improve the code you didn't ask it to improve - these "passing by" casual improvements are always more risky than the main task, as neither of you has the context.
4. Don't let it remove or radically rewrite older comments left in the code. Sometimes it gets carried away like that.
5. Agents have a tendency to overemphasize their recent experiences: for example, if they made a mistake and you corrected it in the chat, they may try to mention this mistake and its correction very specifically in the comments within the code or in the documents. For you it's just a tiny thing that happened in the latest 5 minutes of your multi-decade life, but for them it's 30% of their entire window content. Don't let the agent overshare these minutiae; it is not helpful.

# Advanced Topics

## Beyond a one-shot prompt: Design and Scoping

AI-assisted coding (as any other coding!) works best with small, focused, concrete, scope-limited tasks. If the change you're trying to make is ambitious, try to break your task into several subtasks. For example, when developing a feature, ask the agent to develop a set of good unit tests _first_. Explain the feature, provide a description, let it write some tests (warning it that the tests cannot be run yet, as the feature does not exist yet). Check the tests, make sure you like them. Then give it the second task - writing the feature to satisfy the tests!

An even better approach, which is especially important for large architectural changes, is to disentangle design and implementation stories. You may, for example, try to follow this scenario using these prompts, one after another:

1. (First describe the problem to the agent in some detail) Given the task, examine the code already in the repo. Summarize the current state of it: key classes, usage patterns, design elements, their interactions with the rest of the repo. Check how the current code is tested. Identify and summarize weak and strong aspects of the current design.
2. Given the task and the current code, design the architecture of our new feature (or our refactoring). Come up with several design proposals, for each of them outline their pros and cons, and indicate which one of these you personally recommend.
3. Given the current code and the description of the target design, come up with a list of small atomic steps that would bring us from the current state to the target state. Describe the changes to the tests that will be needed at each incremental step. At the end of your output document, list the acceptance criteria (aka DoD, the Definition of Done)

Once you have the list of atomic incremental steps, you can ask the agent to implement steps 1-4, steps 5-6, etc., reviewing the code at every stage if necessary.

For this entire approach to work, you want to migrate from working with the chat only to working with markdown documents! At each step, create a new `.md` document and ask the agent to output the result to this document (by hashtag-referencing it). Once the output is ready, review it and edit it as needed! Make sure you like it before going to the next step! If the assessment of the code, the design, or the DoD needs correction, correct it. Then, once it's time to proceed, you can either reference this `.md` or copy it in the chat. For example, in case of design proposals, it's better to copy the proposal that you liked in the chat and not include other proposals, as it may erode the context and confuse the agent. If you decide to follow this approach, don't forget to close or unfocus the `.md` to prevent it from getting added to the context "by mistake".

For now, there's no "best practice" for how to organize these markdown files or whether they would need to be saved "for posterity". Most probably, in the next few months it will become normative to save them as part of repo history / documentation, as prompts are generally too verbose to include in either commit messages or PR descriptions, but at the same time they may be important in the future for understanding the motivation behind the changes in the code. For now there is no standard for how to do it. Personally, I name them based on the kanban/scrum story and keep them all in a separate "design" folder within the repo, to be committed together with the code that they generated.

And crucially, in Copilot, because of it aggressive approach to [context compaction](https://www.reddit.com/r/GithubCopilot/comments/1q5k9r6/copilot_cli_vs_claude_code_when_using_the_same_llm/), it's better to _start a new session_ for each new step, then manually reference the files you need, or paste the output of the previous step in the chat window. You want the context to be as free as possible for the agent to do its best work. Sometimes you can combine "explore" and "design" phases in one context, without a chat reset, but if you ever hit the point of context compaction, then it's better not to move to the next step within the same session. (In Copilot you would see the agent pausing with a message "Summarizing conversation history...") Nothing is horribly lost at this point, so you can and should still continue if you are in the middle of some atomic move, and only need to fix the last unit step to be "done" with this little part, but once you can stop, it's better to stop and start a new chat. After the compaction, the agent may start getting confused about some details, and about which files it had read, and which it didn't. Its memories become hazy and approximate. So once the current activity is over, and the agent declares victory over whatever that it was doing, start a new chat and move to the next step with an optimistic and eager newborn agent.

## Adversarial process

Recently, a new approach to developing with an agent was proposed, sometimes referred to as **Iterative Adversarial Refinement** [ref1](https://gist.github.com/dollspace-gay/45c95ebfb5a3a3bae84d8bebd662cc25), [ref2](https://github.com/oaustegard/claude-skills/releases?q=crafting-instructions&expanded=true). In this process, you start by following through the steps described above, but then, once everything is implemented, you add an extra step:

* Do a git diff between this branch and `main` branch. Pretend you're a senior dev doing a code review and you HATE this implementation. Does it even work? Are the requirements satisfied? Are the tests good? Are there any missed edge cases, vulnerabilities, code smells? Is it performant? Is it well designed? Will it be easy to maintain in the long-term? Be tough but fair; if something is good, acknowledge it, but concentrate on weak points. For weaknesses, be reserved and practical: explain why it is bad, then outline the direction of the desired change (what should we do to fix the problem). Lead with the hardest critiques. Output your analysis to NEWFILE.md

Once you receive the critique, analyze it. Classify all identified weaknesses into four groups:

1. Critiques that are not true because the agent doesn't know something that you know (external limitations, future plans etc.)
2. Critiques with which you disagree because they are silly, outright hallucinated, or that don't match your personal taste
3. When 2-3 competing designs are possible, and neither of them is ideal, the critic would be likely to advertise for the 2nd possible choice if you picked the 1st one, and vice versa. It may be right. Or it may be wrong. It's for you to decide, but this is not an good critique by itself.
4. Legitimate good critiques with which you agree

Pick 1-2 legitimate critiques, and ask the agent to implement them. **Then repeat this step!** Keep repeating this step until you no longer have anything in category (4): that is, until all critiques are either made-up (2) or unfair (1, 3).

Critically, to follow this approach you need to start a new session every time and carefully curate the information flow. The critic should always criticize the code _as is_: it should have access _only_ to the code (the output of `git diff` tool) and the description of the feature (either your original prompt or the "acceptance criteria" / DoD that you generated at some point). Nothing else. It should not see the reasoning of the "designer" agent, it should not know any pros and cons that you considered, it should not see the results of the previous critic-improvement iteration; it should always start from scratch and only have the code and the DoD to consider. If it has any extra info, it will get derailed into reiterating old talking points and expanding on the aspects you already considered. To have a fresh look, you need to ask a fresh agent from scratch.

## Documentation for humans

When using agents for _writing documentation_, be triple-careful, as we don't have unit tests for documentation, so we don't have any way to tell if the generated text is "true" in any sense of this word, and even less so if it is good or helpful. At the same time, vague, wordy, obsolete, or hallucinated documentation is a form of technical debt, and an expensive one at that. LLM agents have a reverence for `.md` documents: they tend to believe them more than the code itself, so any lie or obsolete info in the documents may erode the performance of an agent. Yet unless you ask about it very specifically, it won't complain; it will just produce suboptimal code.

So please be very critical, demanding, and deliberate when using agents for writing or editing the docs. The value of a good doc is that it gives you the info you need, but not more. LLMs are not good at achieving this balance. They are bad at generalization, at not going on a tangent. So please, don't let them pollute the docs! Docs are our treasure.

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

Within a single conversation session, the agent remembers what you have just taught it. We may sometimes try to use this. If you feel that the session was particularly productive, or had a strong friction where the agent had to perform a lot of research, or you had to correct it a lot, you may try to use this prompt:

> Let's take a step back and re-group. Re-read your #file:agents.md and think whether you learned or experienced anything new in this session, either from reading the code, or from interacting with me, that warrants an update of your constitution in agents.md? If so, propose your changes.

Compare agent's ideas to the text of `agents.md`. These ideas are almost always bad: too verbose and generous in terms of adding text to this compact document. Agents _can't introspect_ their own state, so as a rule, they cannot generate good prompts for themselves! (yet!) Still, look at the proposal and think about it. If the same kind of problem happens repeatedly, perhaps you could correct or improve some of the rules and boundaries in the `agents.md`
