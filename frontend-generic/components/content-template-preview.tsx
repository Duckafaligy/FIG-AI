import { Check, Sparkles } from "lucide-react";

type Props = { title: string; category: string; topic: string; template: string; revision: number; id: string };

export function ContentTemplatePreview({ title, category, topic, template, revision, id }: Props) {
  const kind = template.startsWith("Blog") ? "blog" : template.startsWith("Resources") ? "tutorial" : "guide";
  const sections = ["Choose one useful outcome", "Build your first version", "Review what comes back", "Make it repeatable"];
  const sectionId = (index: number) => `${id}-section-${index}`;
  return <article className={`detail-cms-frame detail-cms-frame--${kind}`}>
    <div className="detail-cms-nav"><strong>Demo workspace</strong><span>Learn AI</span><span>Guides</span><span>Workflow library</span><a href={`#${sectionId(0)}`}>Start learning</a></div>
    <div className="detail-cms-hero">
      <div><span>{kind === "tutorial" ? "Hands-on tutorial" : category}</span><h4>{title}</h4><p>{revision % 2 === 0 ? `Put ${topic} into practice with a small, repeatable workflow. Follow the example, check the result, and make it your own.` : `Go from a blank page to a useful first result. This guide breaks ${topic} into clear decisions, a worked example, and a review checklist.`}</p><div><small>By Demo workspace team</small><small>·</small><small>May 25, 2025</small><small>·</small><small>4 min read</small></div></div>
      <div className="detail-hero-art" role="img" aria-label="Demo workspace learning guide cover"><span>DW</span><i /><i /><i /></div>
    </div>
    {kind === "tutorial" && <div className="detail-tutorial-summary"><span><b>4 steps</b> to a working first version</span><span><b>You need</b> one task and an AI assistant</span></div>}
    <div className="detail-cms-content">
      <div className="detail-cms-article">
        <p className="detail-cms-lead">The most useful way to learn {topic} is to apply it to something you already do. You do not need a complicated system to begin. Pick one recurring task, define a good result, and test a small version before adding more steps.</p>
        <h5>What you&apos;ll take away</h5>
        <ul><li>A clear brief that explains your goal and audience.</li><li>A reusable prompt with an example you can adapt.</li><li>A review process that keeps you in control of the final result.</li></ul>
        <h5 id={sectionId(0)}>01 · {sections[0]}</h5>
        <p>Start with a task you can finish and review in one sitting. For example, turn a page of meeting notes into a short team update. Decide what the update should contain: the decisions made, the person responsible for each next step, and any unanswered questions.</p>
        <p>Write a one-sentence success criterion: “Someone who missed the meeting can understand the decisions and know what to do next.” This gives you a concrete way to judge the output.</p>
        <div className="detail-cms-callout"><Sparkles size={16} /><span>Demo workspace tip</span><p>Use a short, non-sensitive example for your first test. Check the process before you use it for important work.</p></div>
        <h5 id={sectionId(1)}>02 · {sections[1]}</h5>
        <p>Give the assistant four things: the task, the source material, the audience, and the format. Keep instructions specific enough to evaluate. Instead of asking for a “better summary,” ask for three decisions, a list of next steps, and unresolved questions.</p>
        <div className="detail-prompt-example"><span>Example prompt</span><p>{revision % 2 === 0 ? "Turn the notes below into a team update. Use only the supplied notes. Include: a two-sentence overview, decisions, next steps with owners, and open questions. If an owner or date is missing, write ‘not specified’. Keep the update under 200 words." : "You are preparing a handoff for a teammate who missed our meeting. Read the notes below and create a brief with four headings: Context, Decisions, Actions, and Questions. Preserve names and dates exactly. Flag gaps instead of inventing details."}</p></div>
        <h5 id={sectionId(2)}>03 · {sections[2]}</h5>
        <p>Read the result beside the source. Check names, numbers, dates, and whether every claim is supported. A fluent answer can still leave out a decision or add a detail that was never in the notes. Edit the draft before sending it.</p>
        <ul className="detail-article-checklist">{["Every decision can be traced to the source.", "Owners and deadlines are accurate or marked as missing.", "The tone suits the intended reader.", "The next action is easy to find."].map(item => <li key={item}><Check size={13} />{item}</li>)}</ul>
        <h5 id={sectionId(3)}>04 · {sections[3]}</h5>
        <p>Save the prompt, the source example, and your edited result together. The next time you use the workflow, change one instruction at a time and compare the result. Note which edits you keep making; those are often the best clues for improving your prompt.</p>
        <p>Once the small version works consistently, try it on a second task. Keep the human review step in place. The aim is to spend less time preparing a draft and more time making a sound decision.</p>
        <div className="detail-article-faq"><h5>Common questions</h5><details open><summary>Do I need to know how to code?</summary><p>No. You can test this workflow with a text editor and an AI assistant. Automation can come later, once you understand which steps are useful.</p></details><details><summary>How do I know if the result is good enough?</summary><p>Compare it with your success criterion and original source. If a claim cannot be verified, revise it or leave it out. For specialist work, include a qualified reviewer.</p></details></div>
        <div className="detail-article-related"><span>Continue learning</span><a href={`#${sectionId(1)}`}>Revisit the prompt example →</a><a href={`#${sectionId(2)}`}>Use the review checklist →</a><a href={`#${sectionId(3)}`}>Plan your next iteration →</a></div>
      </div>
      <aside><span>In this guide</span>{sections.map((section, index) => <a href={`#${sectionId(index)}`} key={section}>{section}</a>)}<div><strong>Your next five minutes</strong><small>Choose a task, try the example, and check the result against your source.</small><a href={`#${sectionId(1)}`}>Try the example</a></div></aside>
    </div>
    <div className="detail-cms-footer"><strong>Demo workspace</strong><span>Practical AI skills. One useful step at a time.</span></div>
  </article>;
}
